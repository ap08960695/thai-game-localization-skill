using System;
using System.IO;
using System.Text;

namespace ThaiVoiceOverride
{
    public sealed class Pcm16Wav
    {
        public readonly int Channels;
        public readonly int SampleRate;
        public readonly float[] Samples;
        private Pcm16Wav(int channels, int sampleRate, float[] samples)
        {
            Channels = channels;
            SampleRate = sampleRate;
            Samples = samples;
        }

        public static Pcm16Wav Read(string path)
        {
            using (var stream = File.OpenRead(path)) return Read(stream);
        }

        public static Pcm16Wav Read(Stream stream)
        {
            if (!stream.CanSeek || stream.Length < 12 || stream.Length > 64 * 1024 * 1024)
                throw new InvalidDataException("WAV must be seekable and 12 bytes to 64 MiB");
            using (var reader = new BinaryReader(stream, Encoding.ASCII, true))
            {
                if (Encoding.ASCII.GetString(reader.ReadBytes(4)) != "RIFF") throw new InvalidDataException("Not RIFF");
                long end = reader.ReadUInt32() + 8L;
                if (end != stream.Length || Encoding.ASCII.GetString(reader.ReadBytes(4)) != "WAVE")
                    throw new InvalidDataException("Invalid RIFF size or WAVE signature");
                int channels = 0, rate = 0, align = 0;
                long dataStart = -1;
                int dataSize = 0;
                bool formatFound = false;
                while (stream.Position < end)
                {
                    if (end - stream.Position < 8) throw new InvalidDataException("Truncated chunk header");
                    var tag = Encoding.ASCII.GetString(reader.ReadBytes(4));
                    uint size = reader.ReadUInt32();
                    long start = stream.Position, next = start + size + (size & 1);
                    if (next > end) throw new InvalidDataException("Truncated WAV chunk");
                    if (tag == "fmt ")
                    {
                        if (formatFound || size < 16) throw new InvalidDataException("Invalid fmt chunk");
                        formatFound = true;
                        int format = reader.ReadUInt16();
                        channels = reader.ReadUInt16();
                        uint frequency = reader.ReadUInt32(), byteRate = reader.ReadUInt32();
                        align = reader.ReadUInt16();
                        int bits = reader.ReadUInt16();
                        if (format != 1 || bits != 16 || channels < 1 || channels > 2 || frequency < 8000 || frequency > 192000 ||
                            align != channels * 2 || byteRate != frequency * align)
                            throw new InvalidDataException("Require PCM16 mono/stereo, 8-192 kHz, consistent block/byte rates");
                        rate = (int)frequency;
                    }
                    else if (tag == "data")
                    {
                        if (dataStart >= 0) throw new InvalidDataException("Duplicate data chunk");
                        dataStart = start;
                        dataSize = checked((int)size);
                    }
                    stream.Position = next;
                }
                if (!formatFound || dataStart < 0 || dataSize == 0 || dataSize % align != 0)
                    throw new InvalidDataException("Missing or unaligned PCM data");
                stream.Position = dataStart;
                var samples = new float[dataSize / 2];
                for (int i = 0; i < samples.Length; i++) samples[i] = reader.ReadInt16() / 32768f;
                return new Pcm16Wav(channels, rate, samples);
            }
        }
    }
}
