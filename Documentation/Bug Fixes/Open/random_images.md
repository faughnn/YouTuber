# Random Background Images for Video Compilation

## Issue Description
Currently, the `audio_to_video.py` converter uses a single static background image (`bloody_hell.jpg`) for all TTS audio segments. We want to implement random background image selection that changes only at specific points in the video structure.

## Current Behavior
- Single background image: `C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Assets\Chris_Morris_Images\bloody_hell.jpg`
- All TTS segments use the same background throughout the entire video

## Desired Behavior
Background images should change **ONLY** at the start of `post_clip` segments and are used **ONLY** for TTS audio segments (not during video playbook). The video structure follows this pattern:
```
intro → pre_clip → video → post_clip → pre_clip → video → post_clip → ... → outro
 [BG1]    [BG1]     [VID]    [BG2]      [BG2]     [VID]    [BG3]    [BG3]
```

**Key Requirements - Image Change Behavior:**
- **Images change ONLY at `post_clip` starts**: A new random background image is selected at the beginning of each `post_clip` TTS segment
- **Random images selected from**: `C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Assets\Chris_Morris_Images\` folder
- **Image persists until next `post_clip`**: The same background image is used throughout the sequence:
  - Current `post_clip` TTS segment → following `pre_clip` TTS segment → stays same until next `post_clip`
- **Outro keeps final image**: If it's the end (outro), it keeps using the same background image from the last `post_clip` - NO new selection for outro
- **Background images are ONLY used for TTS segments**: `intro`, `pre_clip`, `post_clip`, `outro`
- **NO background images during `video` segments**: Actual video clips play normally without any background overlay
- **Images are chosen randomly from the Chris Morris collection** (avoiding immediate repeats)

## Implementation Plan

### Phase 1: Image Collection Setup
1. **Create image collection directory structure:**
   ```
   Assets/
   ├── Chris_Morris_Images/
   │   ├── bloody_hell.jpg (existing)
   │   ├── image_001.jpg (new)
   │   ├── image_002.jpg (new)
   │   └── ... (additional images)
   ```

2. **Expand image collection:**
   - Add 5-10 additional Chris Morris or similar themed images to the folder: `C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Assets\Chris_Morris_Images\`
   - All random background images will be selected from this specific folder
   - Ensure all images are 1920x1080 resolution for consistency
   - Validate image quality and format compatibility

### Phase 2: AudioToVideoConverter Enhancement
**File:** `C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Code\Video_Compilator\audio_to_video.py`

#### 2.1 Image Management System
```python
class ImageManager:
    def __init__(self, images_directory):
        self.images_directory = Path(images_directory)
        self.available_images = []
        self.current_image = None
        self.load_images()
    
    def load_images(self):
        """Load all valid images from directory"""
        # Scan for .jpg, .png files
        # Validate image dimensions and format
      def get_random_image(self):
        """Select random image different from current from Chris Morris Images folder"""
        # Return path to randomly selected image from the collection
        # Located at: C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Assets\Chris_Morris_Images\
      def set_image_for_sequence(self, segment_type):
        """Update current image ONLY if segment_type is 'post_clip'
        
        Image change behavior:
        - Changes ONLY at 'post_clip' segment starts
        - Persists through entire sequence until next 'post_clip'
        - Outro keeps the same image from last 'post_clip' (no new selection)
        """
        if segment_type == 'post_clip':
            self.current_image = self.get_random_image()
        # For all other segment types (intro, pre_clip, outro), keep current image
        return self.current_image
```

#### 2.2 AudioToVideoConverter Modifications
```python
class AudioToVideoConverter:
    def __init__(self):
        # Initialize image manager with Chris Morris Images folder
        self.image_manager = ImageManager(
            r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Assets\Chris_Morris_Images"
        )
        self.logger = logging.getLogger(__name__)
    
    def convert_audio_segment(self, audio_path, output_path, segment_type=None):
        """Enhanced method with segment-aware image selection from Chris Morris collection"""
        # Get appropriate background image based on segment type
        background_image = self.image_manager.set_image_for_sequence(segment_type)
        
        # Use background_image in FFmpeg command instead of self.background_image
```

### Phase 3: Integration with Video Compilation Pipeline

#### 3.1 Script Processing Enhancement
The video compilation process needs to pass segment type information to the audio converter:

**File Updates Required:**
- `master_processor_v2.py` - Stage 5 audio generation
- `Chatterbox/simple_tts_engine.py` - TTS processing
- `Video_Compilator/simple_compiler.py` - Compilation orchestration

#### 3.2 Script Parsing for Segment Types
```python
def parse_script_segments(script_path):
    """Extract segment types and their order from unified script"""
    with open(script_path, 'r') as f:
        script_data = json.load(f)
    
    segments = []
    for section in script_data['podcast_sections']:
        segments.append({
            'section_id': section['section_id'],
            'section_type': section['section_type'],
            'order': len(segments)
        })
    
    return segments
```

#### 3.3 Audio Generation Coordination
```python
def generate_audio_with_image_sequence(script_segments):
    """Generate TTS audio segments with coordinated background image selection
    
    Image sequence behavior:
    - Images change ONLY when processing 'post_clip' segments
    - Same image persists through: post_clip → pre_clip → post_clip (new image)
    - Outro segment uses the image from the last post_clip (no new selection)
    """
    image_manager = ImageManager(images_directory)
    
    for segment in script_segments:
        # Only process TTS segments (not video clips)
        if segment['section_type'] in ['intro', 'pre_clip', 'post_clip', 'outro']:
            # Update image selection ONLY for post_clips
            current_image = image_manager.set_image_for_sequence(segment['section_type'])
            
            # Generate TTS audio segment with appropriate background image
            convert_audio_segment(
                audio_path=segment['audio_file'],
                output_path=segment['video_file'], 
                background_image=current_image,
                segment_type=segment['section_type']
            )
        # Video clips (section_type='video_clip') are handled separately 
        # and use the original video content without background images
```

### Phase 4: Testing and Validation

#### 4.1 Unit Tests
- Test `ImageManager` class functionality
- Verify random selection avoids consecutive duplicates
- Validate image sequence tracking

#### 4.2 Integration Tests
- Test full pipeline with random images
- Verify image changes occur only at `post_clip` boundaries
- Confirm image consistency within sequences

#### 4.3 Visual Validation
- Generate test video with multiple post_clips
- Manual review to confirm:
  - Background images used only for TTS segments (intro, pre_clip, post_clip, outro)
  - Video clips play normally without any background overlay
  - **Background images change ONLY at the start of post_clip TTS segments**
  - **Same background image maintained during entire sequence: post_clip → pre_clip → (next post_clip gets new image)**
  - **Outro segment keeps the same image from the last post_clip (no new image selection)**
  - No background images appear during video clip playback

## Technical Considerations

### Image Quality Requirements
- All images must be exactly 1920x1080 resolution
- Supported formats: .jpg, .png
- File size considerations for processing speed
- Color/contrast suitable for text overlay (if applicable)

### Performance Impact
- Image loading and selection overhead
- FFmpeg processing time with different images
- Memory usage with multiple image files

### Error Handling
- Fallback to default image if random selection fails
- Validation of image file integrity
- Graceful handling of missing image files

### Configuration Options
```python
# Configuration settings to add
VIDEO_SPECS = {
    "width": 1920,
    "height": 1080,
    "fps": "29.97",
    "codec": "libx264",
    "random_backgrounds": True,  # New option
    "background_change_points": ["post_clip"]  # Configurable
}
```

## Files to Modify

### Primary Changes
1. `Code/Video_Compilator/audio_to_video.py` - Core image management
2. `Code/master_processor_v2.py` - Pipeline coordination
3. `Code/Chatterbox/simple_tts_engine.py` - TTS integration

### Supporting Changes
4. `Code/Video_Compilator/simple_compiler.py` - Compilation logic
5. `Code/Config/default_config.yaml` - Configuration options

### Testing Files
6. Create test script for image management functionality
7. Create integration test for full pipeline with random images

## Success Criteria
- ✅ Background images used ONLY for TTS segments (intro, pre_clip, post_clip, outro)
- ✅ Video clips play normally without background image overlay
- ✅ Background images change **ONLY** at `post_clip` TTS segment starts
- ✅ Same background image maintained throughout entire sequence: post_clip → pre_clip → (next post_clip gets new image)
- ✅ **Outro segment keeps the same image from last post_clip (no new image selection)**
- ✅ Random selection without immediate repeats
- ✅ No performance degradation in video generation
- ✅ Backward compatibility with single image mode
- ✅ Proper error handling and fallbacks

## Risk Assessment
- **Low Risk:** Changes are isolated to image selection logic
- **Medium Risk:** Integration with existing pipeline requires careful coordination
- **Mitigation:** Extensive testing and gradual rollout with fallback options

## Implementation Priority
**Priority:** Medium
**Effort:** 2-3 days
**Dependencies:** None blocking

## Notes
- Consider adding configuration option to disable random images
- Future enhancement: Theme-based image selection based on content analysis
- Potential for user-defined image collections per episode type
