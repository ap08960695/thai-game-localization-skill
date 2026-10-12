using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using BepInEx;
using HarmonyLib;
using UnityEngine;

namespace ThaiVoiceOverride
{
    [BepInPlugin(Id, "ThaiVoiceOverride", "0.1.0")]
    public sealed class Plugin : BaseUnityPlugin
    {
        private const string Id = "example.game.thai.voiceoverride";
        // Adapt these identifiers after inspecting the target build's shared voice iterator.
        private const string VoiceContainerType = "GAME_VOICE_CONTAINER_TYPE";
        private const string VoiceCoroutinePrefix = "<GAME_VOICE_COROUTINE>";
        private static Plugin instance;
        // shortcut: clips stay cached until restart; add eviction only for a measured memory need.
        private readonly Dictionary<string, AudioClip> clips = new Dictionary<string, AudioClip>();
        private Harmony harmony;
        private string voiceFolder;

        private void Awake()
        {
            Logger.LogInfo("INIT ThaiVoiceOverride");
            try
            {
                var root = Path.GetFullPath(Path.Combine(Paths.PluginPath, "ThaiVoiceOverride"));
                var folder = Config.Bind("General", "VoiceFolder", "voices",
                    "Relative subfolder inside BepInEx/plugins/ThaiVoiceOverride; restart after changing.").Value;
                voiceFolder = Path.GetFullPath(Path.Combine(root, folder));
                if (!voiceFolder.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("VoiceFolder must be a subfolder of " + root);
                var voiceType = AccessTools.TypeByName(VoiceContainerType);
                if (voiceType == null) throw new TypeLoadException(VoiceContainerType);
                var iterator = voiceType.GetNestedTypes(BindingFlags.Public | BindingFlags.NonPublic)
                    .Single(t => t.Name.StartsWith(VoiceCoroutinePrefix, StringComparison.Ordinal));
                var target = AccessTools.Method(iterator, "MoveNext");
                if (target == null) throw new MissingMethodException(iterator.FullName, "MoveNext");
                instance = this;
                harmony = new Harmony(Id);
                Logger.LogInfo("PATCH " + target.DeclaringType.FullName + ".MoveNext");
                harmony.Patch(target, transpiler: new HarmonyMethod(typeof(Plugin), nameof(ReplaceAssignment)));
                Logger.LogInfo("READY voice iterator -> AudioSource.clip; voices=" + voiceFolder);
            }
            catch (Exception error)
            {
                harmony?.UnpatchSelf();
                Logger.LogError("Override disabled; original playback retained: " + error);
            }
        }

        private static IEnumerable<CodeInstruction> ReplaceAssignment(IEnumerable<CodeInstruction> instructions)
        {
            var code = instructions.ToList();
            var setter = AccessTools.PropertySetter(typeof(AudioSource), nameof(AudioSource.clip));
            var matches = code.Where(i => i.Calls(setter)).ToList();
            if (matches.Count != 1)
                throw new InvalidOperationException("Expected exactly one voice clip assignment; found " + matches.Count);
            // Keep labels and exception blocks on the existing instruction.
            matches[0].opcode = OpCodes.Call;
            matches[0].operand = AccessTools.Method(typeof(Plugin), nameof(AssignVoiceClip));
            return code;
        }

        private static void AssignVoiceClip(AudioSource source, AudioClip original)
        {
            var selected = original;
            var id = original == null ? "" : original.name;
            try
            {
                if (string.IsNullOrEmpty(id) || id.Any(c => !(char.IsLetterOrDigit(c) || c == '_')))
                    instance.Logger.LogInfo("LOOKUP MISS unsafe-id=" + id);
                else
                {
                    var path = Path.Combine(instance.voiceFolder, id + ".wav");
                    if (!File.Exists(path)) instance.Logger.LogInfo("LOOKUP MISS " + id + " -> original");
                    else
                    {
                        instance.Logger.LogInfo("LOOKUP HIT " + id + " file=" + path);
                        if (!instance.clips.TryGetValue(id, out selected))
                        {
                            var wav = Pcm16Wav.Read(path);
                            selected = AudioClip.Create(id, wav.Samples.Length / wav.Channels,
                                wav.Channels, wav.SampleRate, false);
                            try
                            {
                                if (!selected.SetData(wav.Samples, 0))
                                    throw new InvalidDataException("AudioClip.SetData failed");
                            }
                            catch
                            {
                                Destroy(selected);
                                throw;
                            }
                            instance.clips.Add(id, selected);
                        }
                        instance.Logger.LogInfo("OVERRIDE " + id + " duration=" + selected.length +
                            " rate=" + selected.frequency + " channels=" + selected.channels);
                    }
                }
            }
            catch (Exception error)
            {
                instance.Logger.LogWarning("FALLBACK " + id + " -> original: " + error.Message);
                selected = original;
            }
            source.clip = selected;
        }

        private void OnDestroy()
        {
            harmony?.UnpatchSelf();
            foreach (var clip in clips.Values) Destroy(clip);
            clips.Clear();
            if (instance == this) instance = null;
        }
    }
}
