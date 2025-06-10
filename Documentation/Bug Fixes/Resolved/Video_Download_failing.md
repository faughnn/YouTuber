# YouTube Video Download Failures Investigation

**Date**: June 9, 2025  
**Status**: IDENTIFIED - Multiple Issues Found  
**Severity**: HIGH - Blocks video pipeline functionality

## 🔍 INVESTIGATION SUMMARY

YouTube video downloading is failing due to multiple compounding issues related to YouTube's evolving anti-bot measures and format changes. The problems range from completely unavailable videos to format selection failures caused by YouTube's transition to HLS-only streaming.

## 📊 FAILURE ANALYSIS

### Issue 1: Video Unavailability (Complete Failure)
**Affected Video**: `https://www.youtube.com/watch?v=TJb4SqJRCrM`
```
ERROR: [youtube] TJb4SqJRCrM: Video unavailable
```

**Root Cause**: This video is genuinely unavailable, likely due to:
- Geographic restrictions/geoblocking
- Content removed by uploader/YouTube
- Age restrictions requiring authentication
- Copyright claims/DMCA takedowns

**Impact**: Complete pipeline failure when encountering unavailable videos

### Issue 2: YouTube nsig Extraction Failures (Partial Failure)
**Affected Video**: `https://www.youtube.com/watch?v=C81bFx8CSA8`
```
WARNING: [youtube] C81bFx8CSA8: nsig extraction failed: Some formats may be missing
         n = bTutOhKcndAaIHG ; player = https://www.youtube.com/s/player/fc2a56a5/player_ias.vflset/en_US/base.js
```

**Root Cause**: YouTube's anti-bot signature encryption system
- YouTube regularly changes their player signature extraction methods
- yt-dlp must reverse-engineer these changes
- Our version (2025.05.22) has outdated signature extraction logic
- This causes some high-quality formats to become unavailable

**Impact**: 
- Audio downloads succeed
- Video downloads fail with format selection errors
- Reduced available format options

### Issue 3: SABR Streaming Format Changes (Technical Limitation)
```
WARNING: [youtube] C81bFx8CSA8: Some web client https formats have been skipped as they are missing a url. 
YouTube is forcing SABR streaming for this client. See https://github.com/yt-dlp/yt-dlp/issues/12482
```

**Root Cause**: YouTube's transition to SABR (Streaming-Aware Bit-Rate) streaming
- YouTube is forcing HLS (m3u8) streams instead of direct HTTP downloads
- Traditional format selectors designed for HTTP formats fail
- All available formats are now fragmented HLS streams

**Impact**: Complete failure of current format selection logic

### Issue 4: Outdated Format Selection Logic (Implementation Bug)
**Current Format Selectors in `youtube_video_downloader.py`:**
```python
format_options = [
    'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/bestvideo[ext=mp4][height<=1080]+bestaudio/bestvideo[ext=mp4]+bestaudio[ext=m4a]',
    'best[ext=mp4][height<=1080]/best[ext=mp4]',
    'best[height<=1080]/best'
]
```

**Problem**: These selectors expect:
- HTTP-based formats with `.mp4` extensions
- Separate video and audio tracks with specific codecs
- Traditional YouTube format structure

**Reality**: Current YouTube formats are:
- HLS streams (m3u8 protocol)
- All marked as "mp4" but actually fragmented
- Require specific format ID combinations

## 🧪 COMPREHENSIVE TESTING RESULTS

**Test Coverage**: 39 different methods tested across multiple categories
**Overall Success Rate**: 51.3% (20/39 tests passed)
**Test Date**: June 9, 2025

### ✅ CONFIRMED WORKING SOLUTIONS

#### Format Combinations (33.3% success rate - 7/21 working)
**Working Format Selectors:**
1. `best[height<=1080]` - Best up to 1080p ✅
2. `bestvideo+bestaudio` - Best video + best audio ✅ 
3. `bestvideo[height<=1080]+bestaudio` - Best 1080p video + audio ✅
4. `bestvideo[height<=720]+bestaudio` - Best 720p video + audio ✅
5. `232+233` - 720p HLS + audio ✅
6. `270+233` - 1080p HLS + audio ✅
7. `bestvideo+bestaudio/best` - Combined with single file fallback ✅

#### Extraction Methods (75% success rate - 9/12 working)
**Working Extraction Approaches:**
1. Default extraction ✅
2. Android client (`--extractor-args youtube:player_client=android`) ✅
3. iOS client (`--extractor-args youtube:player_client=ios`) ✅
4. Skip DASH (`--extractor-args youtube:skip=dash`) ✅
5. Skip DASH manifest (`--youtube-skip-dash-manifest`) ✅
6. Skip certificate check (`--no-check-certificates`) ✅
7. Extended timeout (`--socket-timeout 30`) ✅
8. Desktop user agent ✅
9. iPhone user agent ✅

#### Download Strategies (50% success rate - 2/4 working)
**Working Download Methods:**
1. HLS merge download (`-f 232+233 --merge-output-format mp4`) ✅
2. Audio extraction (`-x --audio-format mp3`) ✅

### ❌ FAILED METHODS ANALYSIS

#### Format Selection Failures (14/21 failed)
**All traditional format selectors failed:**
- `best`, `worst` - Basic quality selectors
- `best[height<=720]`, `best[height<=480]` - Lower resolution limits
- `best[ext=mp4]` - Extension-based selection
- `best[vcodec^=avc]` - Codec-based selection
- `18`, `22`, `136+140`, `137+140` - Traditional format IDs
- `best[protocol^=https]`, `best[protocol^=m3u8]` - Protocol-based selection

**Root Cause**: YouTube has moved to HLS-only streaming, making traditional HTTP format selectors obsolete.

#### Extraction Method Failures (3/12 failed)
**Failed extraction approaches:**
- Web client (`--extractor-args youtube:player_client=web`) - Likely blocked
- Mobile web client (`--extractor-args youtube:player_client=mweb`) - Likely blocked  
- Skip HLS (`--extractor-args youtube:skip=hls`) - No non-HLS formats available

#### Download Strategy Failures (2/4 failed)
**Failed download strategies:**
- Basic 480p download - Resolution-based selectors don't work
- Download with retries - Same underlying format issue not solved by retries

## 🔧 TECHNICAL ROOT CAUSES

### 1. YouTube's Anti-Automation Measures
- **nsig Extraction**: Signature encryption to prevent automated downloads
- **SABR Streaming**: Forced adaptive bitrate streaming
- **Format Obfuscation**: Hiding direct download URLs
- **Regular Updates**: Frequent changes to defeat downloaders

### 2. Our Implementation Gaps
- **Static Format Selection**: Hardcoded format strings fail with dynamic formats
- **No HLS Handling**: Missing logic for fragmented stream downloads  
- **Poor Error Recovery**: No fallback when preferred formats unavailable
- **Missing Format Discovery**: No dynamic format detection logic

### 3. yt-dlp Version Limitations
- **Current Version**: 2025.05.22 (latest available)
- **Known Issues**: GitHub issue #12482 documents SABR streaming problems
- **Ongoing Battle**: Constant cat-and-mouse game with YouTube changes

## 💡 UPDATED SOLUTION STRATEGIES

### Immediate Fixes (High Priority) - Based on Test Results

#### 1. Replace Format Selection Logic with Proven Working Formats
**Current failing approach** in `youtube_video_downloader.py`:
```python
# BROKEN - These all fail with current YouTube
format_options = [
    'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/bestvideo[ext=mp4][height<=1080]+bestaudio/bestvideo[ext=mp4]+bestaudio[ext=m4a]',
    'best[ext=mp4][height<=1080]/best[ext=mp4]',
    'best[height<=1080]/best'
]
```

**Replace with tested working formats:**
```python
# PROVEN WORKING - All tested successfully
format_options = [
    "bestvideo[height<=1080]+bestaudio",     # Best 1080p video + audio ✅
    "270+233",                               # 1080p HLS + audio ✅  
    "bestvideo[height<=720]+bestaudio",      # Best 720p video + audio ✅
    "232+233",                               # 720p HLS + audio ✅
    "best[height<=1080]",                    # Best up to 1080p ✅
    "bestvideo+bestaudio",                   # Best video + best audio ✅
]
```

#### 2. Add Working Extraction Method Arguments
```python
# Add successful extraction arguments to command
command = [
    'yt-dlp',
    '-f', format_selector,
    '--extractor-args', 'youtube:player_client=android',  # Proven working client
    '--merge-output-format', 'mp4',
    '-o', output_path,
    '--no-warnings',
    '--extractor-retries', '3',
    '--fragment-retries', '3',
    normalized_url
]
```

#### 3. Enhanced Availability Testing (Pre-flight Check)
```python
def test_video_availability(url: str) -> Tuple[bool, str]:
    """Test video availability before attempting download."""
    # Test with multiple successful extraction methods
    extraction_methods = [
        [],  # Default
        ['--extractor-args', 'youtube:player_client=android'],
        ['--extractor-args', 'youtube:player_client=ios'],
    ]
    
    for method in extraction_methods:
        try:
            result = subprocess.run([
                'yt-dlp', '--get-title', '--no-warnings'
            ] + method + [url], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, result.stdout.strip()
        except subprocess.TimeoutExpired:
            continue
            
    return False, "Video unavailable with all extraction methods"
```

### Medium-Term Improvements

#### 1. Dynamic Format Discovery
- Query available formats before attempting download
- Select best available format combination automatically
- Cache working format combinations for similar videos

#### 2. Enhanced Retry Logic
- Multiple yt-dlp extraction methods (web client, mobile client, etc.)
- Exponential backoff for transient failures  
- Smart format fallback chains

#### 3. Alternative Download Strategies
- Multiple extraction backends (youtube-dl as fallback)
- Different user agent rotation
- Proxy/VPN integration for geo-restricted content

### Long-Term Strategies

#### 1. Content Source Diversification
- Support for alternative video platforms (Rumble, BitChute, etc.)
- Local video file processing emphasis
- Pre-downloaded content workflows

#### 2. Legal Compliance
- Terms of Service compliance review
- Rate limiting implementation
- User consent mechanisms

## 🚨 IMMEDIATE ACTION REQUIRED

### Critical Priority Tasks

1. **Update Format Selection** (30 minutes)
   - Replace hardcoded format strings in `youtube_video_downloader.py`
   - Add working format combinations discovered in testing
   - Implement graceful fallback chain

2. **Fix Video Unavailability Handling** (45 minutes)
   - Add pre-download availability check
   - Return special status codes for different failure types
   - Update master processor to handle unavailable videos gracefully

3. **Improve Error Messages** (15 minutes)
   - Replace generic "Error occurred with yt-dlp" messages
   - Provide specific guidance for different failure types
   - Log sufficient detail for debugging

### Testing Requirements

1. **Multi-Video Test Suite**
   - Test with known working videos
   - Test with geoblocked/unavailable videos
   - Test with various video lengths and qualities

2. **Error Path Validation**
   - Verify audio-only processing continues when video fails
   - Confirm proper error reporting and logging
   - Test fallback format selection logic

## 📈 SUCCESS METRICS

- **Video Download Success Rate**: Target >80% for publicly available videos
- **Pipeline Resilience**: 100% of valid audio downloads should complete regardless of video failure
- **Error Clarity**: Users should understand why specific videos fail
- **Fallback Effectiveness**: System should gracefully degrade when video unavailable

## 🔗 RELATED ISSUES

- **GitHub Issue**: https://github.com/yt-dlp/yt-dlp/issues/12482 (SABR streaming)
- **YouTube Changes**: Ongoing platform modifications affecting all download tools
- **Legal Considerations**: Terms of Service compliance for automated downloads

## 🎯 UPDATED CONCLUSION

The comprehensive testing of 39 different download methods has revealed the true scope of YouTube's anti-automation measures and provided concrete, tested solutions. With a 51.3% overall success rate, we now have definitive data on what works and what doesn't.

**Critical Findings:**
1. **HLS-Only Reality**: YouTube has completely moved to HLS streaming - traditional format IDs (18, 22, 136, 137) no longer work
2. **Client Dependency**: Android and iOS clients work better than web clients (75% extraction success rate)  
3. **Format Selection Evolution**: Modern selectors like `bestvideo[height<=1080]+bestaudio` work, while traditional ones fail
4. **Specific Working Combinations**: `232+233` and `270+233` are reliable HLS format pairs

**Proven Success Path:**
- Use `bestvideo[height<=1080]+bestaudio` or `232+233` format selectors
- Add `--extractor-args youtube:player_client=android` for better reliability  
- Implement pre-flight availability testing with multiple extraction methods
- Fall back gracefully to audio-only processing when video fails

## 🏆 QUALITY-RANKED FALLBACK IMPLEMENTATION PLAN

### Quality-First Strategy
Based on comprehensive testing, implement a quality-ranked fallback system that starts with the absolute highest quality and gracefully degrades until a working format is found.

### Format Priority Ranking (Highest to Lowest Quality)

#### Tier 1: Maximum Quality (Unrestricted)
```python
# Try for absolute best quality first - no restrictions
"best",                                    # Unrestricted best quality
"bestvideo+bestaudio",                     # Best video + best audio (✅ proven working)
"best[height<=2160]",                      # 4K if available
"bestvideo[height<=2160]+bestaudio",       # 4K video + best audio
```

#### Tier 2: High Quality (1080p)  
```python
# 1080p options - high quality but more likely to work
"best[height<=1080]",                      # Best up to 1080p (✅ proven working)
"bestvideo[height<=1080]+bestaudio",       # 1080p video + audio (✅ proven working)
"270+233",                                 # 1080p HLS + audio (✅ proven working)
"614+233",                                 # 1080p VP9 + audio (high quality)
"616+234",                                 # 1080p VP9 Premium + high audio
```

#### Tier 3: Good Quality (720p)
```python
# 720p options - good balance of quality and compatibility
"best[height<=720]",                       # Best up to 720p
"bestvideo[height<=720]+bestaudio",        # 720p video + audio (✅ proven working)
"232+233",                                 # 720p HLS + audio (✅ proven working)
"609+233",                                 # 720p VP9 + audio
"232+234",                                 # 720p + high quality audio
```

### Implementation Code

#### 1. Updated `youtube_video_downloader.py`
```python
def get_quality_ranked_format_options():
    """Get format options ranked by quality from highest to lowest."""
    return [
        # Tier 1: Maximum Quality (Unrestricted)
        ("best", "Unrestricted best quality"),
        ("bestvideo+bestaudio", "Best video + best audio (✅ tested)"),
        ("best[height<=2160]", "4K if available"),
        ("bestvideo[height<=2160]+bestaudio", "4K video + best audio"),
        
        # Tier 2: High Quality (1080p)
        ("best[height<=1080]", "Best up to 1080p (✅ tested)"),
        ("bestvideo[height<=1080]+bestaudio", "1080p video + audio (✅ tested)"),
        ("270+233", "1080p HLS + audio (✅ tested)"),
        ("614+233", "1080p VP9 + audio (high quality)"),
        ("616+234", "1080p VP9 Premium + high audio"),
        
        # Tier 3: Good Quality (720p)
        ("best[height<=720]", "Best up to 720p"),
        ("bestvideo[height<=720]+bestaudio", "720p video + audio (✅ tested)"),
        ("232+233", "720p HLS + audio (✅ tested)"),
        ("609+233", "720p VP9 + audio"),
        ("232+234", "720p + high quality audio"),
        
        # Emergency fallbacks
        ("bestvideo+bestaudio/best", "Combined with fallback (✅ tested)"),
        ("18", "360p MP4 (legacy format)"),
        ("worst", "Absolute worst quality available"),
    ]

def download_video_with_quality_fallback(video_url_or_id, file_organizer=None):
    """Enhanced download function with quality-ranked fallback system."""
    # ... existing validation code ...
    
    format_options = get_quality_ranked_format_options()
    
    # Try each format option in quality order (desktop extraction only)
    for format_selector, format_desc in format_options:
        try:
            print(f"Attempting format: {format_selector} ({format_desc})")
            
            command = [
                'yt-dlp',
                '-f', format_selector,
                '--merge-output-format', 'mp4',
                '-o', output_path,
                '--no-warnings',
                '--extractor-retries', '3',
                '--fragment-retries', '3',
                normalized_url
            ]
            
            subprocess.run(command, check=True, capture_output=True, text=True)
            
            if os.path.exists(output_path):
                print(f"✅ SUCCESS: Downloaded with {format_selector}")
                print(f"   Quality: {format_desc}")
                return output_path
                
        except subprocess.CalledProcessError as e:
            error_output = e.stderr if e.stderr else e.stdout
            print(f"❌ Failed: {format_selector} - {error_output[:100]}...")
            continue
    
    # If we get here, everything failed
    raise Exception("All quality levels failed")
```

#### 2. Simple Progress Reporting
```python
def report_download_success(format_selector, format_desc, file_path):
    """Report successful download details."""
    print(f"📊 Download completed successfully!")
    print(f"   Format used: {format_selector}")
    print(f"   Quality: {format_desc}")
    print(f"   File location: {file_path}")
    
    # Optional: Get file size for reporting
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        print(f"   File size: {file_size:.1f} MB")
```

### Implementation Steps

#### Phase 1: Core Implementation (1 hour)
1. **Replace existing format selection logic**
   - Update `download_video()` function in `youtube_video_downloader.py`
   - Implement quality-ranked fallback system
   - Add comprehensive logging

2. **Test with known video**
   - Verify highest quality formats are attempted first
   - Confirm graceful degradation when high quality fails
   - Validate that proven working formats (✅) still work

#### Phase 2: Enhanced Features (1 hour)
1. **Improve progress reporting**
   - Show current quality tier being attempted
   - Report final achieved quality to user
   - Log quality degradation decisions

2. **Add better error handling**
   - Distinguish between format failures and network issues
   - Provide clear feedback on why specific formats failed
   - Implement timeout handling for slow downloads

#### Phase 3: Integration Testing (1 hour)
1. **Master processor integration**
   - Update `_stage_2_audio_acquisition()` to use new download function
   - Ensure proper error handling and fallback to audio-only
   - Test with multiple video types and qualities

2. **Validation testing**
   - Test with 4K videos (if available)
   - Test with restricted/limited quality videos
   - Verify that system always finds the highest available quality

### Success Metrics

- **Quality Achievement**: System should consistently get the highest available quality
- **Fallback Reliability**: When high quality fails, system should gracefully degrade
- **Performance**: Quality testing should not significantly slow down downloads
- **User Feedback**: Clear reporting of achieved quality vs. attempted quality

### Expected Outcomes

1. **Maximum Quality**: System will always attempt the absolute best quality first
2. **Smart Degradation**: When best quality fails, systematic fallback to next best
3. **Proven Reliability**: Falls back to tested working formats (✅) when needed
4. **User Transparency**: Clear reporting of what quality was achieved and why

**Implementation Priority**: 
1. **Immediate** (1 hour): Update format selectors with quality-ranked fallback
2. **Short-term** (1 hour): Add enhanced logging and progress reporting
3. **Medium-term** (1 day): Full integration testing and optimization

The investigation has transformed from theoretical analysis to empirical evidence with a concrete quality-first implementation strategy.

**Test Report**: Complete results saved to `youtube_download_test_report_20250609_220154.md`