# Installing Auto-Editor

## Method 1 (Recommended)

Get the offical binary, available on Windows, MacOS, and x86_64 Linux.

1. go to the [Releases page](https://github.com/WyattBlue/auto-editor/releases) on GitHub, and download the binary for your platform.
2. rename the binary to auto-editor (or auto-editor.exe for Windows).
3. In the terminal/PowerShell, `cd` into your downloads folder.

If you're on MacOS/Linux, run:

```
chmod +x ./auto-editor
```

1. Run Auto-Editor in the terminal. Because the binaries are unsigned, you may get "Unknown developer" warnings. Ignore them.

Congratulations, auto-editor should now be installed. To verify auto-editor is installed, run:

```
./auto-editor --help
```

It's recommended to place the binary in a PATH directory so that `auto-editor` is always available no matter your current working directory.

## Method 2: Platform Installers

If you're on MacOS, it's recommend to use [Homebrew](https://homebrew.sh/):

```
brew install auto-editor
```

Auto-Editor is available on apt:

```
sudo apt install auto-editor
```

Auto-Editor is available on the Arch Linux AUR:

```
yay -S auto-editor
```

## Method 3: Pip

Notice: It is not recommended to use this method because new versions of auto-editor are no longer being published on pip.

First, download and install [Python](https://python.org/)

> If you are installing on Windows, make sure "Add Python 3.x to PATH" is checked.

Once that's done, you should have pip on your PATH. That means when you run `pip` on your console, you should get a list of commands and not `command not found`. If you don't have pip on your PATH, try reinstalling Python.

Then run:

```
pip install auto-editor
```

Now run this command and it should list all the options you can use

```
auto-editor --help
```

If that works then congratulations, you have successfully installed auto-editor. You can use now use this with any other type of video or audio that you have.

```
auto-editor C:path\to\your\video.mp4
```

If you would like to uninstall auto-editor, run:

```
pip uninstall auto-editor
```

## Installing from Source (unix-like):

Install nim, make sure `nimble` is available. You'll also need cmake, meson, and ninja.

```
nimble makeff  # Downloads and builds all dependencies
nimble make
```

## Installing from Source (Windows)

To build an `.exe`, you'll need to install [WSL](https://learn.microsoft.com/en-us/windows/wsl/about), then install nim on that environment. Make sure `nimble` is available. You'll also need cmake, meson, and ninja.

Then run:

```
nimble makeffwin
nimble windows
```

## Optional Dependencies

If yt-dlp is installed, auto-editor can download and use URLs as inputs.

```
auto-editor "https://www.youtube.com/watch?v=kcs82HnguGc"
```

How yt-dlp is installed does not matter.

# Actions

Actions define what auto-editor does to different parts of your media. By default, inactive (silent) sections are cut out and active (loud) sections are kept unchanged. Actions give you fine-grained control over this behavior.

## Basic Syntax

Actions are specified using the `--when-silent` and `--when-normal` options:

```bash
# Cut silent sections (default behavior)
auto-editor video.mp4 --when-silent cut

# Keep normal sections unchanged (default behavior)
auto-editor video.mp4 --when-normal nil
```

These options have aliases:

- `--when-silent` = `--when-inactive`, `-w:0`
- `--when-normal` = `--when-active`, `-w:1`

## Available Actions

### nil

**Syntax:** `nil`

Do nothing. Keep the section unchanged at normal speed with normal pitch.

```bash
# Keep everything, even silent sections
auto-editor video.mp4 --when-silent nil
```

### cut

**Syntax:** `cut`

Remove the section completely from the output.

```bash
# Remove silent sections (default behavior)
auto-editor video.mp4 --when-silent cut

# Remove loud sections (inverted editing)
auto-editor video.mp4 --when-normal cut
```

### speed

**Syntax:** `speed:<value>`

Change the playback speed while preserving pitch using time-stretching.

- **Value range:** 0.0 to 99999.0

```bash
# Speed up silent sections to 8x (preserving pitch)
auto-editor video.mp4 --when-silent speed:8

# Slow down normal sections to half speed
auto-editor video.mp4 --when-normal speed:0.5
```

**How it works:** Uses FFmpeg's `atempo` filter to change speed without affecting pitch.

### varispeed

**Syntax:** `varispeed:<value>`

Change the playback speed by varying pitch, like analog tape or vinyl.

- **Value range:** 0.2 to 100.0

```bash
# Speed up silent sections with pitch variation
auto-editor video.mp4 --when-silent varispeed:2

# Create slow-motion effect with lower pitch
auto-editor video.mp4 --when-normal varispeed:0.5
```

**How it works:** Uses FFmpeg's `asetrate` + `aresample` filters to change sample rate, which changes both speed and pitch together.

### volume

**Syntax:** `volume:<value>`

Adjust the audio volume level.

- **1.0** = normal volume
- **0.5** = half volume (-6dB)
- **2.0** = double volume (+6dB)

```bash
# Reduce silent section volume to 20%
auto-editor video.mp4 --when-silent volume:0.2

# Boost loud sections
auto-editor video.mp4 --when-normal volume:1.5
```

### invert

**Syntax:** `invert`

Invert all pixels in the video section.

```bash
auto-editor video.mp4 --when-silent invert
```

### zoom

**Syntax:** `zoom:<value>`

Zoom in or out by a factor.

- **Value range:** greater than 0.0, up to 100.0
- **1.0** = no zoom

```bash
# Zoom in 2x on active sections
auto-editor video.mp4 --when-normal zoom:2

# Zoom out on silent sections
auto-editor video.mp4 --when-silent zoom:0.5
```

## Multiple Actions (Chaining)

You can combine multiple actions using commas. Actions are applied in the order specified.

```bash
# Speed up AND reduce volume
auto-editor video.mp4 --when-silent speed:3,volume:0.5

# Combine speed and varispeed
# Effective speed: 1.25 × 1.25 = 1.5625x
auto-editor video.mp4 --when-normal varispeed:1.25,speed:1.25

# Triple action: speed, varispeed, and volume
auto-editor video.mp4 --when-silent speed:2,varispeed:1.5,volume:0.8
```

## Setting Actions for a Time Range

Use `--set-action` to apply an action to a specific time range, overriding the default actions:

```bash
# Keep a section unchanged from 0 to 5 seconds
auto-editor video.mp4 --set-action nil,0,5sec

# Apply speed + varispeed from 30 seconds to the end
auto-editor video.mp4 --set-action speed:1.5,varispeed:1.5,30sec,end
```

The format is `ACTION,START,END` where `ACTION` can be any action or comma-separated list of actions.

## Common Use Cases

### Fast-Forward Through Silence

```bash
auto-editor video.mp4 --when-silent speed:8
```

### Subtle Speed Variations

```bash
# Slightly slow down normal sections for emphasis
auto-editor video.mp4 --when-normal speed:0.9
```

### Duck Audio During Silence

```bash
# Keep silent sections but reduce volume
auto-editor video.mp4 --when-silent volume:0.3
```

### Podcast Editing

```bash
# Cut silence, slightly speed up speech
auto-editor podcast.mp3 --when-silent cut --when-normal speed:1.15
```

### Music Editing

```bash
# Keep everything but boost quiet parts
auto-editor song.mp3 --when-silent volume:1.8 --when-normal volume:1.0
```

### Creative Effects

```bash
# Nightcore effect: speed up and pitch up
auto-editor video.mp4 --when-normal varispeed:1.25

# Slow-mo with deep voice
auto-editor video.mp4 --when-normal varispeed:0.75

# Fast silent sections with reduced volume
auto-editor video.mp4 --when-silent speed:6,volume:0.4
```

## Deprecated Options

The following options are deprecated but still supported:

```bash
# Old way (deprecated)
auto-editor video.mp4 --silent-speed 8 --video-speed 1

# New way (preferred)
auto-editor video.mp4 --when-silent speed:8 --when-normal speed:1
```

## See Also

- [Range Syntax](https://auto-editor.com/docs/range-syntax) - Manual editing with `--cut-out` and `--add-in`
- [Audio Normalization](https://auto-editor.com/docs/anorm) - Volume normalization options

# Audio Normalizing

Audio normalization is the process of adjusting audio levels to achieve consistent loudness across your media. This is especially useful when combining multiple audio sources with different volume levels, or when preparing content for platforms that have specific loudness requirements.

Auto-Editor supports two kinds of audio normalization: **peak** and **ebu**. Peak normalization is simpler and faster, scaling audio based on the highest amplitude. EBU R128 normalization is more sophisticated, analyzing perceived loudness to meet broadcast standards. Choose peak normalization for quick volume adjustments, or EBU normalization when you need precise loudness control for professional distribution.

## Peak

Example:

```
auto-editor --audio-normalize peak:-3  # set max peak to -3dB
```

The key idea is that peak normalization preserves the dynamic range of your audio—it just scales everything up or down so the loudest moment hits your target level. This is different from EBU normalization which analyzes perceived loudness over time.

## EBU

EBU R128 normalization analyzes the perceived loudness of your audio over time and adjusts it to meet broadcast standards. Unlike peak normalization which simply scales the audio, EBU normalization uses a more sophisticated algorithm that considers how humans perceive loudness.

Example:

```
auto-editor --audio-normalize ebu  # use default values
auto-editor --audio-normalize ebu:i=-16  # set integrated loudness target
auto-editor --audio-normalize "ebu:i=-5,lra=20,gain=5,tp=-1"  # customize all parameters
```

### Parameters

- **i** (integrated loudness): Target integrated loudness in LUFS (Loudness Units Full Scale)
  - Default: `-24.0`
  - Range: `-70.0` to `5.0`
  - Common values: `-23` (EBU R128), `-16` (streaming), `-14` (podcasts)
- **lra** (loudness range): Target loudness range in LU
  - Default: `7.0`
  - Range: `1.0` to `50.0`
  - Describes the variation between soft and loud passages
- **tp** (true peak): Maximum true peak level in dBTP
  - Default: `-2.0`
  - Range: `-9.0` to `0.0`
  - Prevents clipping during digital-to-analog conversion
- **gain**: Additional gain offset in dB
  - Default: `0.0`
  - Range: `-99.0` to `99.0`
  - Applied on top of the loudness normalization

### How It Works

EBU normalization uses a two-pass process:

1. **Analysis Pass**: Measures the integrated loudness, loudness range, and true peak of the entire audio
2. **Normalization Pass**: Applies the FFmpeg `loudnorm` filter with the measured values to normalize the audio to your target levels

This approach ensures consistent perceived loudness across different audio content, making it ideal for broadcast, streaming platforms, and podcast production.

# How To Shrink File Size

## Auto-Editor Makes Files That Are Too Big!

This is generally good since auto-editor tries to preserve video quality as much as possible. However, there are tricks you can use to shrink file size with little to no quality loss.

## Video Bitrate

Change the video bitrate to a lower value. Auto-Editor by default sets the video bitrate to `5M` or 5 Megabytes. This is a very high bitrate so most video encoders will use a lower value, however, the encoder still might set a bitrate too high for your liking. You can set it manually based on the file size you expect.

Assuming the video is 2 minutes, the file size will be about 27600k (2 * 60 * 230), not including audio size.

```
auto-editor my-video.mp4 -b:v 230k
```

Examples:

```
auto-editor my-huge-h264-video.mp4 -b:v 10M  # Maximum quality, big file size
auto-editor my-h264-video.mp4 -b:v auto  # Let ffmpeg chose, efficient and good looking quality
auto-editor i-want-this-tiny.mp4 -b:v 125k  # Set bitrate to 125 kilobytes, quality may vary
auto-editor my-video.mp4 -c:v h264 -b:v 0  # Set a variable bitrate
```

## Audio Streams

Your audio contributes to size too, if you use the AAC encoder, it should always be a reasonable size.

| Encoder               | Type             | Quality   | Speed     |
| --------------------- | ---------------- | --------- | --------- |
| aac_at (AudioToolBox) | Hardware (Apple) | best      | very fast |
| fdk_aac               | Software         | very good | fast      |
| aac (ffmpeg)          | Software         | good      | fast      |

## Using Better Video Encoders

Your file size depends on the encoder used. h264 is great but not the best. hevc (also known as h265) can achieve much smaller sizes with about the same quality. One trade-off is that some software, such as media players and editors, doesn't the next-gen encoders.

The table below compares different video codecs:

| Codecs | Compression | Speed     | Compatibility |
| ------ | ----------- | --------- | ------------- |
| h264   | high        | very fast | best          |
| hevc   | very high   | fast*     | so-so         |
| vp9    | very high   | slow      | high          |
| av1    | very high   | very slow | high          |
| mpeg4  | very low    | superfast | so-so         |

Due to copyright and patent law affecting software makers, auto-editor does not bundle hevc software encoders, but you can re-encode your videos if you have your own ffmpeg installed.

Example:

```
ffmpeg -i my-video.mp4 -c:a copy -c:v hevc -b:v 0 my-video-h265.mp4
```

## Tips for libx264

Auto-Editor doesn't ship libx264 for legal reasons, but you can still use x264 if you have ffmpeg installed.

```
ffmpeg -i input.mp4 -c:a copy -c:v libx264 -preset medium out.mp4
```

Use Constant Rate Factor (CRF) unless you already know exactly what you want the bitrate to be. Setting `-preset` to a slower value than `medium` doesn't hurt either.

If you do use video bitrate, don't set it to a high number like `10M`. Unlike libopenh264, libx264 with faithfully target that absurd number even if the quality gain is teeny-tiny.

[FFmpeg's wiki page explains the options you can use in more detail.](https://trac.ffmpeg.org/wiki/Encode/H.264)

# Subcommands

Subcommands are auxiliary programs that offer additional functionality. They have their own options, separate from the main auto-editor cli.

```
About
The cache command stores the audio and motion levels, saving time at the cost of space. The cache will go up to 10 entires, and will delete the oldest after.

Examples
To list the cache files:

auto-editor cache
To remove the cache files:

auto-editor cache clear
```

```
desc
desc displays the video's description. If there is none, No description. will be displayed.

Examples:

% yt-dlp --add-metadata -f "bestvideo[ext=mp4]" "https://www.youtube.com/watch?v=jNQXAC9IVRw" -o out.mp4
% auto-editor desc out.mp4

Chapters:

00:00 Intro
00:05 The cool thing
00:17 End

Interesting.... https://www.youtube.com/watch?v=VaLXzI92t9M
% auto-editor desc example.mp4

No description.
```

```
info
info is a utility program that displays media information relevant to auto-editor.

Here is an example. Note that you can use multiple files at once.

auto-editor info example.mp4 resources/only-video/man-on-green-screen.gif

example.mp4:
 - video:
   - track 0:
     - codec: h264
     - fps: 30
     - resolution: 1280x720
     - aspect ratio: 16:9
     - pixel aspect ratio: 1:1
     - duration: 42.400000
     - pix fmt: yuv420p
     - color range: tv
     - color space: bt709
     - color primaries: bt709
     - color transfer: bt709
     - timebase: 1/30000
     - bitrate: 240958
     - lang: eng
 - audio:
   - track 0:
     - codec: aac
     - samplerate: 48000
     - channels: 2
     - duration: 42.400000
     - bitrate: 317375
     - lang: eng
 - container:
   - duration: 42.400000
   - bitrate: 570335

resources/only-video/man-on-green-screen.gif:
 - video:
   - track 0:
     - codec: gif
     - fps: 30
     - resolution: 1280x720
     - aspect ratio: 16:9
     - pixel aspect ratio: 1:1
     - duration: 24.410000
     - pix fmt: bgra
     - timebase: 1/100
 - container:
   - duration: 24.410000
   - bitrate: 1649917
The default format is pseudo-yaml meant for humans. You can get a machine friendly output with the --json option.

auto-editor info example.mp4 --json

{
    "example.mp4": {
        "type": "media",
        "video": [
            {
                "codec": "h264",
                "fps": "30",
                "resolution": [
                    1280,
                    720
                ],
                "aspect_ratio": [
                    16,
                    9
                ],
                "pixel_aspect_ratio": "1:1",
                "duration": "42.400000",
                "pix_fmt": "yuv420p",
                "color_range": "tv",
                "color_space": "bt709",
                "color_primaries": "bt709",
                "color_transfer": "bt709",
                "timebase": "1/30000",
                "bitrate": "240958",
                "lang": "eng"
            }
        ],
        "audio": [
            {
                "codec": "aac",
                "samplerate": 48000,
                "channels": 2,
                "duration": "42.400000",
                "bitrate": "317375",
                "lang": "eng"
            }
        ],
        "subtitle": [

        ],
        "container": {
            "duration": "42.400000",
            "bitrate": "570335",
            "fps_mode": null
        }
    }
}
You may call info with aeinfo.
```

```
levels
levels displays individual "edit method" stream values before the threshold procedure (if any) is applied. media information relevant to auto-editor. levels mainly exists to be used extensively by other programs so they can use auto-editor's rich media analysis features.

Because typical levels output is so long, it won't be displayed verbatim.

auto-editor levels example.mp4

@start
0.00008813678829543451
0.00026441036488630354
0.00026441036488630354
0.00017627357659086903
0.00775603736999823726
0.04794641283271637577
0.14604265820553499755
0.44368059227921735621
0.52362065926317646891
0.46201304424466771437
0.47611493037193725053
0.51427815970386037137
0.86162524237616777700
0.76291203948528119039
0.70853164110699806688
(Continues for 1000 more lines)
0.18905341089370703012
0.02793936188965273973
0.01401374933897408734
0.01189846641988365900
0.00493566014454433280
0.00317292437863564251
0.00105764145954521417
0.00008813678829543451
0.00008813678829543451
0.00000000000000000000
0.00000000000000000000
(30 more lines)
0.00000000000000000000
0.00000000000000000000
0.00000000000000000000
0.00000000000000000000

levels uses --edit to determine what is being analyzed, which by default is audio.
```

```
subdump
subdump is a utility program that displays the textual representation of subtitle streams in media files.

Here's an example:

auto-editor subdump resources/subtitle.mp4

file: resources/subtitle.mp4 (0:und:srt)
1
00:00:00,523 --> 00:00:01,016
oop

2
00:00:01,523 --> 00:00:01,916
boop


------
subdump won't work if the subtitle stream is internally represented as a bitmap image instead of formatted text.
```

# Supported Media

Auto-Editor supports a wide range of media formats thanks to ffmpeg. Listed below is what is and is not allowed.

## What's allowed

- Media with only audio streams
- Media with only video streams
- Media with video, audio, subtile, embedded images, and data streams

## What isn't

- Media with only subtitle/data streams.
- Media with video or audio streams longer than 24 hours
- Video streams whose total number of frames exceeds a 60fps 24 hour video
- Audio streams whose total number of samples exceeds a 192kHz 24 hour video

Using specific codecs/containers depends on which ffmpeg program auto-editor uses.

------

### Footnotes

The terms "stream" and "track" are used interchangeably.

# Range Syntax

## How Do I Cut the Beginning or End Segment in My Video?

Range syntax is useful for making manual edits in addition to automatic edits. Here's how you cut out the first and last 30 seconds:

```
auto-editor video.mp4 --cut-out start,30sec -30sec,end
```

You can also guarantee those sections would be included, regardless of loudness with:

```
auto-editor video.mp4 --add-in start,30sec -30sec,end
```

## How Range Syntax Works

The `--add-in`, `--cut-out`, `--mark-as-loud`, `--mark-as-silent` options all use time range syntax.

It describes two numbers, the start and end point, separated by a singe comma `,`. The start number is inclusive, while the end number is exclusive.

```
# This will cut out the first frame: frame 0
auto-editor example.mp4 --cut-out 0,1

# This will cut out five frames: frames 0, 1, 2, 3, 4
# frame 5 will still exist because the end point is exclusive
auto-editor example.mp4 --cut-out 0,5

# Cuts out 60 frames
auto-editor example.mp4 --cut-out 10,70

# No frame will be cut here
auto-editor example.mp4 --cut-out 0,0
```

## Variables

Time range syntax allows two variables: `start` and `end` `start` is the same as `0` `end` is the length of the timeline before any edits are applied.

```
# This will mark everything in the beginning as silent
auto-editor example.mp4 --mark-as-silent start,300

# This will mark everything besides the beginning as loud
auto-editor example.mp4 --mark-as-loud 300,end

# This will cut out everything
auto-editor example.mp4 --cut-out start,end
```

## Units

The default unit is the timeline's timebase. Since specifying the range in this unit can sometimes be annoying. You can use the `sec` unit to specify the range in seconds. (Note that the seconds range will be rounded to the nearest timebase to you don't have any more precision than usual).

```
# Cut out the first 10 seconds.
auto-editor example.mp4 --cut-out start,10secs
```

You can also use `s`, `sec`, `second`, or `seconds`, depending on your preference.

## Multiple Ranges

All options discussed here support specifying multiple ranges at the same time. Overlapping ranges are allowed.

```
auto-editor example.mp4 --cut-out 0,20 45,60, 234,452
```

## Negative Indexes

Negative numbers can be used to count down starting from the end.

- `-60,end` selects the last 60 frames
- `1sec,-30secs` selects from the first second, to the last 30 seconds from the end.

## Speed for Range

The `--set-speed-for-range` option has a slight twist on time range syntax. It accepts three numbers. `speed`, `start`, and `end`, separated by commas. `speed` can be a decimal number, but not negative. `start` and `end` work as described above.

```
# Set the speed to 2x from frame 0 to frame 29
auto-editor example.mp4 --set-speed-for-range 2,0,30

# Set the speed to 0.5x
auto-editor example.mp4 --set-speed-for-range 0.5,start,end
```

# The v1 format

## Overview

The v1 format is the simplest way to represent a timeline. It supports cutting and changing speed from `0.0` to `99999.0` inclusive. v1 is a stable format. Developers are welcome to use it to make cuts for auto-editor and to use it for their own programs.

You can generate a v1 timeline file with `auto-editor example.mp4 --export timeline:api=1` and it would look something like this:

```json
{
  "version": "1",
  "source": "example.mp4",
  "chunks": [
    [0, 26, 1],
    [26, 34, 0],
    [34, 396, 1],
    [396, 410, 0],
    ...
  ],
}
```

v1 is a subset of [JSON](https://www.json.org/). `...` is used to show that a variable amount of elements are allowed.

Auto-Editor can use the v1 format as input:

```
auto-editor input.json -o output.mkv
```

## Limitations

Only a single file (source) is allowed. Additionally, v1 only supports "linear" timelines. That means sections further in the media cannot be put ahead in the timeline than sections before.

## The Spec

There are only three keys that are required: `"version"`, `"source"`, and `"chunks"`. If there are more keys present in the JSON, the parser should ignore them.

shown using TypeScript notation, the keys can be set to the following values.

```ts
interface v1 {
  version: "1";    // Must always be set as "1".

  source: string;  // Path to a media file. The path can be relative or absolute,
                   // but must be valid for the given platform.

  chunks: Chunk[]; // We'll cover this in the next section.
}
```

## Chunks

Each `Chunk` element has 3 parts:

- start: When from the media to start playing
- end: When from the media to stop playing
- speed: How fast to play (or cut) the section.

`start` (inclusive) and `end` (exclusive) represent a time range: selecting a segment from the original source. There is no hard limit how big `start` and `end` can be.

The speed 1.0 means to play the media at its normal rate. The speeds 99999.0 and 0.0 always mean cut a section off/don't include it.

It is valid for `chunks` to be an empty array. The first `chunk` must start with 0. All other `chunk`s must have their `start` set be the preceding `end`'s value (there can be no gaps).

## The Implicit Timebase

`start` and `end` are in the timebase unit. Timebase determines how much actual time a length occurs. To determine the timebase, divide 1 by the average framerate of the source.

For example, if suppose `input.mp4` has a framerate of `30/1`, then `1/30` is the timebase. A chunk of `[0, 1, 1.0]` would then have a length of 1/30 of a second.

# The v3 format

## Overview

The v3 format is a nonlinear timeline file format. It supports multiple overlapping video and audio layers. The v3 format is a subset of [JSON](https://www.json.org/), and the proper extension is `.json`.

Auto-Editor can generate v3 timelines from media files (instructed with `--edit`),

```
auto-editor example.mp4 --export timeline:api=3 -o input-v3.json
```

render media files from the v3 format,

```
auto-editor input-v3.json -o output.mkv
```

and translate other timeline formats to v3:

```
auto-editor input-fcp7.xml --export timeline:api=3 -o output-v3.json
```

## Stability

This format is considered partially-stable. Breaking changes can be made to feature level changes, but not patch level changes.

## The Header

shown using TypeScript notation, the keys can be set to the following values.

```ts
type Integer = number; // An integer floating-point value.
type Natural = number; // An integer floating-point value that is >= 0.
type Source = string; // A path to a media file, must be valid for the given platform.
type SupportedSpeed = float; // Between 0.0 exclusive and 99999.0 exclusive.

interface v3 {
  version: "3";       // Must always be set as "3".
  resolution: [number, number];  // width and height. Must both be natural numbers.
  timebase: string;   // The timebase. Must be a rational number.
                      // Typical values are: "24/1", 30/1", "30000/1001"
                      // Values with a decimal ("29.97") should be rejected.

  samplerate: number; // The overall samplerate, must be a natural number.

  background: string; // A web RGB color value for the background. Relevant in cases
                      // like when a video has a different aspect ratio than the..
                      // global resolution. Must be in the format "#000" or "#000000".
   v: Video[][];
   a: Audio[][];
}
```

## Video and Audio Layers

The elements in the `v` and `a` keys are a tagged union with `name` as the discriminant.

```ts
interface Video {
  name: "video";
  src: Source;
  start: Natural;   // Where in this timeline to start this clip. In terms of timebase.
  dur: Natural;     // The duration of the clip. In terms of timebase.
  offset: Natural;  // Where from the source to start playing at. In terms of timebase.
  speed: SupportedSpeed;
  stream: Natural;  // Which video stream from the source to use.
                    // Usually stream 0.
}

interface Audio {
  name: "audio";
  src: Source;
  start: Natural;
  dur: Natural;
  offset: Natural;
  volume: float;    // A float between 0.0 and 1.0. Changes the audio loudness.
  stream: Natural;  // Which audio stream from the source to use.
}
```

The v3 format looks something like this:

```json
{
  "version": "3",
  "resolution": [1280, 720],
  "timebase": "30/1",
  "samplerate": 48000,
  "background": "#000",
  "v": [
    [
      {
        "name": "video",
        "src": "example.mp4",
        "start": 0,
        "dur": 26,
        "offset": 0,
        "speed": 1.0,
        "stream": 0
      },
      {
        "name": "video",
        "src": "example.mp4",
        "start": 26,
        "dur": 362,
        "offset": 34,
        "speed": 1.0,
        "stream": 0
      },
      ...
    ]
  ],
  "a": [
    [
      {
        "name": "audio",
        "src": "example.mp4",
        "start": 0,
        "dur": 26,
        "offset": 0,
        "speed": 1.0,
        "volume": 1,
        "stream": 0
      },
      {
        "name": "audio",
        "src": "example.mp4",
        "start": 26,
        "dur": 362,
        "offset": 34,
        "speed": 1.0,
        "volume": 1,
        "stream": 0
      },
      ...
    ]
  ]
}
```

There are two additional video elements:

```ts
// Draw an image
interface Image {
  name: "image";
  src: Source;
  start: Natural;   // Where in this timeline to start this clip. In terms of timebase.
  dur: Natural;     // The duration of the clip. In terms of timebase.
  x: Integer;
  y: Integer;
  width: Natural;
  opacity: float;
}

// Draw a rectangle with a solid color
interface Rect {
  name: "rect";
  start: Natural;
  dur: Natural;
  x: Integer;
  y: Integer;
  width: Natural;
  height: Natural;
  fill: string;
}
```

# [CLI Options](https://auto-editor.com/ref/options) — Describes auto-editor's command line options

## Editing Options:

### `--edit METHOD`

#### Aliases: `-e`

Set an expression which determines how to make auto edits. (default is "audio")

### `--when-normal ACTION`

#### Aliases: `-w:1` `--when-active`

When a segment is active (defined by --edit) do an action. The default action being 'nil'

### `--when-silent ACTION`

#### Aliases: `-w:0` `--when-inactive`

When a segment is inactive (defined by --edit) do an action. The default action being 'cut'

Actions available:

nil, unchanged/do nothing

cut, remove completely

speed, (val: float),

```
change the speed while preserving pitch. val: between (0-99999)
```

varispeed, (val: float),

```
change the speed by varying pitch. val: between [0.2-100]
```

invert, invert all pixels in a video

zoom, (val: float),

```
zoom in/out with a factor of val. val: between (0-100]
```

### `--margin LENGTH[,LENGTH?]`

#### Aliases: `-m`

Set sections near "loud" as "loud" too if section is less than LENGTH away. (default is "0.2s")

### `--smooth MINCUT[,MINCLIP?]`

Make sections 'smoother' by applying minimum cut and minimum clip rules. (default is 0.2s,0.1s)

Examples:

--smooth 0.2s,0.1s # Set mincut to 0.2 seconds, minclip to 0.1 seconds.

--smooth 0 # Turn off smoothing

### `--output FILE`

#### Aliases: `-o`

Set the name/path of the new output file

### `--cut [START,STOP ...]`

#### Aliases: `--cut-out`

Set segment(s) that will be cut/removed

### `--keep [START,STOP ...]`

#### Aliases: `--add-in`

Set segment(s) that are leaved "as is", overriding other actions

### `--set-speed-for-range [SPEED,START,STOP ...]`

#### Aliases: `--set-speed`

Set segment(s) to a SPEED, overriding other actions

### `--set-action ACTION,start,end`

Set a time segment to an ACTION, overriding other actions

Examples:

--set-action nil,0,5sec

--set-action speed:1.5,varispeed:1.5,30sec,end

### `--silent-speed NUM`

[Deprecated] Set speed of inactive segments to NUM. (default is 99999)

### `--video-speed NUM`

[Deprecated] Set speed of active segments to NUM. (default is 1)

## Timeline Options:

### `--frame-rate NUM`

#### Aliases: `-tb` `--time-base` `-r` `-fps`

Set timeline frame rate

### `--sample-rate NAT`

#### Aliases: `-ar`

Set timeline sample rate

### `--resolution WIDTH,HEIGHT`

#### Aliases: `-res`

Set timeline width and height

### `--background COLOR`

#### Aliases: `-b` `-bg`

Set the background as a solid RGB color

## URL Download Options:

### `--yt-dlp-location PATH`

Set a custom path to yt-dlp

### `--download-format FORMAT`

Set the yt-dlp download format (--format, -f)

### `--output-format TEMPLATE`

Set the yt-dlp output file template (--output, -o)

### `--yt-dlp-extras CMD`

Add extra options for yt-dlp. Must be in quotes

## Display Options:

### `--progress PROGRESS`

Set what type of progress bar to use

### `--debug`

Show debugging messages and values

### `--quiet`

#### Aliases: `-q`

Display less output

### `--stats`

#### Aliases: `--preview`

Show stats on how the input will be cut and halt

## Container Settings:

### `-vn`

Disable the inclusion of video streams

### `-an`

Disable the inclusion of audio streams

### `-sn`

Disable the inclusion of subtitle streams

### `-dn`

Disable the inclusion of data streams

### `--faststart`

Enable movflags +faststart, recommended for web (default)

### `--no-faststart`

Disable movflags +faststart, will be faster for large files

### `--fragmented`

Use fragmented mp4/mov to allow playback before video is complete. See: ffmpeg.org/ffmpeg-formats.html#Fragmentation

### `--no-fragmented`

Do not use fragmented mp4/mov for better compatibility (default)

## Video Rendering:

### `--video-codec ENCODER`

#### Aliases: `-c:v` `-vcodec`

Set video codec for output media

### `--video-bitrate BITRATE`

#### Aliases: `-b:v`

Set the number of bits per second for video

### `-crf NUM`

Set the Constant Rate Factor for quality-based encoding. Lower = better quality. [0-63]

### `-vprofile PROFILE`

#### Aliases: `-profile:v`

Set the video profile. For h264: high, main, or baseline

### `--scale NUM`

Scale the output video's resolution by NUM factor

### `--no-seek`

Disable file seeking when rendering video. Helpful for debugging desync issues

## Audio Rendering:

### `--audio-codec ENCODER`

#### Aliases: `-c:a` `-acodec`

Set audio codec for output media

### `--audio-layout LAYOUT`

#### Aliases: `-layout`

Set the audio layout for the output media/timeline

### `--audio-bitrate BITRATE`

#### Aliases: `-b:a`

Set the number of bits per second for audio

### `--mix-audio-streams`

Mix all audio streams together into one

### `--audio-normalize NORM-TYPE`

#### Aliases: `-anorm`

Apply audio normalizing (either ebu or peak). Applied right before rendering the output file

## Miscellaneous:

### `--no-cache`

Disable reading and writing cache files

### `--open`

Open the output file after editing is done

### `--no-open`

Do not open the output file after editing is done (default)

### `--license-key`

#### Aliases: `-k`

Provide a license key, which activates certain features

### `--temp-dir PATH`

Set where the temporary directory is located

### `--version`

#### Aliases: `-V` `-v`

Show info about this program or option

------

Version 30.1.5
Generated: 2026-04-17.

# [Edit](https://auto-editor.com/ref/edit) - How `--edit` Works

# Edit Reference

When you run:



```
auto-editor example.mp4 --edit audio:0.05,stream=0
```

You're writing the syntax-sugary equivalent of:

```
auto-editor example.mp4 --edit "(audio 0.05 #:stream 0)"
```

All the edit methods are listed below:

## Edit Methods

(**audio** *[threshold]* *[stream]*) → [bool-array?](https://auto-editor.com/ref/edit#bool-array?) Procedure

 *threshold*: Threshold = 0.04

 *stream*: (U Natural 'all) = 'all

Do a one-pass audio filter based on loudest sample in a timebase section, divided by the max value a sample can be.

(**motion** *[threshold]* *[stream]* *[blur]* *[width]*) → [bool-array?](https://auto-editor.com/ref/edit#bool-array?) Procedure

 *threshold*: Threshold = 0.02

 *stream*: Natural = 0

 *blur*: Natural = 9

 *width*: Natural = 400

Scale the video to *width* pixels, convert to grayscale, apply a Gaussian blur of *blur* amount, then compare the difference with the previous frame.

(**subtitle** *pattern* *[stream]* *[ignore-case]* *[max-count]*) → [bool-array?](https://auto-editor.com/ref/edit#bool-array?) Procedure

 *pattern*: String

 *stream*: Natural = 0

 *ignore-case*: Bool = #f

 *max-count*: (U Natural Nil) = nil

When *pattern*, a RegEx Expression, matches a subtitle line, consider that time the line occupies as loud.

## Operators

(**or** *operand* *...*) → [bool-array?](https://auto-editor.com/ref/edit#bool-array?) Procedure

 *operand*: [bool-array?](https://auto-editor.com/ref/edit#bool-array?)

"Logical Or" two or more boolean arrays. If they are different lengths, use the biggest one.

(**and** *operand* *...*) → [bool-array?](https://auto-editor.com/ref/edit#bool-array?) Procedure

 *operand*: [bool-array?](https://auto-editor.com/ref/edit#bool-array?)

"Logical And" two or more boolean arrays.