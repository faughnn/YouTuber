import sys
import os
from master_processor_v2 import MasterProcessorV2
from Utils.logger_factory import get_menu_logger
from Utils.enhanced_pipeline_logger import LogLevel

# Enhanced menu system using Rich formatting
menu_logger = get_menu_logger()

# Global verbosity setting (can be changed from menu)
CURRENT_VERBOSITY = LogLevel.NORMAL

STAGE_NAMES = [
    "Media Extraction",
    "Transcript Generation", 
    "Content Analysis",
    "Narrative Generation",
    "Audio Generation",
    "Video Clipping",
    "Video Compilation"
]

# Enhanced menu functions using Rich formatting
def print_main_menu(youtube_url):
    """Display main menu using enhanced logger."""
    menu_logger.show_main_menu(youtube_url)

def get_tts_provider_choice():
    """Prompt user to select TTS provider."""
    print("\n🎤 TTS Provider Selection")
    print("1. Chatterbox TTS (Free)")
    print("2. ElevenLabs TTS (Paid - Higher Quality)")
    choice = input("Select TTS provider (1-2): ").strip()
    return "elevenlabs" if choice == "2" else "chatterbox"

def get_narrative_format_choice():
    """Prompt user to select narrative format."""
    narrative_format = None
    while True:
        menu_logger.show_narrative_format_menu()
        format_choice = input("Enter a number (0-2): ").strip()
        if format_choice == "0":
            menu_logger.show_info("Pipeline cancelled.")
            return None
        elif format_choice == "1":
            narrative_format = "with_hook"
            break
        elif format_choice == "2":
            narrative_format = "without_hook"
            break
        else:
            menu_logger.show_invalid_choice(format_choice, 2)
    return narrative_format

def print_end_at_menu():
    """Display end-at-stage menu using enhanced logger."""
    menu_logger.show_end_at_menu(STAGE_NAMES)

def print_start_from_menu():
    """Display start-from-stage menu using enhanced logger."""
    menu_logger.show_start_from_menu(STAGE_NAMES)

def print_single_stage_menu():
    """Display single stage menu using enhanced logger."""
    menu_logger.show_single_stage_menu(STAGE_NAMES)

# --- Episode Selection ---
def list_episodes(content_dir):
    episodes = []
    for show in os.listdir(content_dir):
        show_path = os.path.join(content_dir, show)
        if not os.path.isdir(show_path):
            continue
        for episode in os.listdir(show_path):
            episode_path = os.path.join(show_path, episode)
            if os.path.isdir(episode_path):
                rel_path = os.path.relpath(episode_path, content_dir)
                episodes.append(rel_path)
    return episodes

def select_episode(content_dir):
    episodes = list_episodes(content_dir)
    if not episodes:
        menu_logger.show_error("No episodes found in Content directory.")
        return None
        
    menu_logger.show_episode_selection(episodes)
    
    while True:
        choice = input(f"Enter a number (1-{len(episodes)}) or 0: ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(episodes):
            selected_episode = episodes[int(choice)-1]
            menu_logger.show_info(f"Selected episode: {selected_episode}", "Episode Selected")
            return selected_episode
        menu_logger.show_invalid_choice(choice, len(episodes))

# --- Pipeline Logic (stubs, to be filled in as needed) ---
def run_pipeline_end_at(processor, youtube_url):
    print_end_at_menu()
    while True:
        choice = input(f"Enter a number (1-7) or 0: ").strip()
        if choice == "0":
            return
        if choice.isdigit() and 1 <= int(choice) <= 7:
            if not youtube_url:
                menu_logger.show_error("You must enter a YouTube URL first! Go back and set it.")
                return
            
            end_stage = int(choice)
            tts_provider = "chatterbox"  # Default
            narrative_format = None  # Default
            
            # If Stage 4 is included, prompt for narrative format at the very start
            if end_stage >= 4:
                narrative_format = get_narrative_format_choice()
                if narrative_format is None:  # User cancelled
                    return
            
            # If Stage 5 is included, prompt for TTS provider at the very start
            if end_stage >= 5:
                tts_provider = get_tts_provider_choice()
            
            # Call your pipeline logic here
            stage_name = STAGE_NAMES[end_stage-1]
            menu_logger.show_processing_start(f"Pipeline (ending at stage {choice})", f"Stages 1-{choice}: {stage_name}")
            
            # TODO: Add actual pipeline execution logic here with tts_provider and narrative_format parameters
            menu_logger.show_info(f"Would run stages 1 to {choice} for URL: {youtube_url} with TTS: {tts_provider.upper()}" + 
                                 (f" and narrative format: {narrative_format}" if narrative_format else ""))
            return
        menu_logger.show_invalid_choice(choice, 7)

def run_pipeline_start_from(processor, content_dir):
    def ensure_dict(val, is_video=False):
        import ast
        if isinstance(val, dict):
            return val
        if isinstance(val, str) and os.path.isdir(val):
            manifest = {'output_directory': val}
            if is_video:
                mp4_files = [f for f in os.listdir(val) if f.lower().endswith('.mp4')]
                manifest['total_clips'] = len(mp4_files)
                manifest['files'] = mp4_files
            return manifest
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        return {'output_directory': val}
    
    episode = select_episode(content_dir)
    if not episode:
        return
    episode_path = os.path.join(content_dir, episode)
    processor.episode_dir = episode_path  # Set the episode_dir for correct context
    print_start_from_menu()
    
    while True:
        choice = input(f"Enter a number (1-7) or 0: ").strip()
        if choice == "0":
            return
def run_pipeline_start_from(processor, content_dir):
    def ensure_dict(val, is_video=False):
        import ast
        if isinstance(val, dict):
            return val
        if isinstance(val, str) and os.path.isdir(val):
            manifest = {'output_directory': val}
            if is_video:
                mp4_files = [f for f in os.listdir(val) if f.lower().endswith('.mp4')]
                manifest['total_clips'] = len(mp4_files)
                manifest['files'] = mp4_files
            return manifest
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        return {'output_directory': val}
    
    episode = select_episode(content_dir)
    if not episode:
        return
    episode_path = os.path.join(content_dir, episode)
    processor.episode_dir = episode_path  # Set the episode_dir for correct context
    print_start_from_menu()
    
    while True:
        choice = input(f"Enter a number (1-7) or 0: ").strip()
        if choice == "0":
            return
        if choice.isdigit() and 1 <= int(choice) <= 7:
            start_stage = int(choice)
            
            # If Stage 4 is included, prompt for narrative format at the very start
            narrative_format = None
            if start_stage <= 4:
                narrative_format = get_narrative_format_choice()
                if narrative_format is None:  # User cancelled
                    return
            
            # If Stage 5 is included, prompt for TTS provider at the very start
            tts_provider = "chatterbox"  # Default
            if start_stage <= 5:
                tts_provider = get_tts_provider_choice()
            
            # Sequentially run from start_stage to 7
            s2 = s3 = s4 = s5 = s6 = s7 = None
            if start_stage <= 2:
                default_audio_path = os.path.join(episode_path, 'Input', 'original_audio.mp3')
                audio_path = default_audio_path if os.path.exists(default_audio_path) else input(f"Enter path to audio file (default: {default_audio_path}): ").strip() or default_audio_path
                s2 = processor._stage_2_transcript_generation(audio_path)
                print(f"Stage 2 complete: {s2}")
            if start_stage <= 3:
                default_transcript_path = os.path.join(episode_path, 'Processing', 'original_audio_transcript.json')
                transcript_path = default_transcript_path if os.path.exists(default_transcript_path) else input(f"Enter path to transcript file (default: {default_transcript_path}): ").strip() or default_transcript_path
                s3 = processor._stage_3_content_analysis(transcript_path)
                print(f"Stage 3 complete: {s3}")
            if start_stage <= 4:
                default_analysis_path = os.path.join(episode_path, 'Processing', 'original_audio_analysis_results.json')
                analysis_path = default_analysis_path if os.path.exists(default_analysis_path) else input(f"Enter path to analysis file (default: {default_analysis_path}): ").strip() or default_analysis_path
                # Use the narrative_format selected at the start
                s4 = processor._stage_4_narrative_generation(analysis_path, narrative_format)
                print(f"Stage 4 complete: {s4}")
            if start_stage <= 5:
                default_script_path = os.path.join(episode_path, 'Output', 'Scripts', 'unified_podcast_script.json')
                script_path = default_script_path if os.path.exists(default_script_path) else input(f"Enter path to script file (default: {default_script_path}): ").strip() or default_script_path
                s5 = processor._stage_5_audio_generation(script_path, tts_provider)
                print(f"Stage 5 complete: {s5}")
            if start_stage <= 6:
                default_script_path = os.path.join(episode_path, 'Output', 'Scripts', 'unified_podcast_script.json')
                script_path = default_script_path if os.path.exists(default_script_path) else input(f"Enter path to script file (default: {default_script_path}): ").strip() or default_script_path
                s6 = processor._stage_6_video_clipping(script_path)
                print(f"Stage 6 complete: {s6}")
            if start_stage <= 7:
                default_audio_results = os.path.join(episode_path, 'Output', 'Audio')
                default_clips_manifest = os.path.join(episode_path, 'Output', 'Video')
                audio_results_path = default_audio_results if os.path.exists(default_audio_results) else input(f"Enter path to audio results (dict or file) (default: {default_audio_results}): ").strip() or default_audio_results
                clips_manifest_path = default_clips_manifest if os.path.exists(default_clips_manifest) else input(f"Enter path to clips manifest (dict or file) (default: {default_clips_manifest}): ").strip() or default_clips_manifest
                s5 = ensure_dict(audio_results_path)
                s6 = ensure_dict(clips_manifest_path, is_video=True)
                s7 = processor._stage_7_video_compilation(s5, s6)
                print(f"Stage 7 complete: {s7}")
            return
        menu_logger.show_invalid_choice(choice, 7)

def run_pipeline_one_stage(processor, content_dir):
    episode = select_episode(content_dir)
    if not episode:
        return
    episode_path = os.path.join(content_dir, episode)
    processor.episode_dir = episode_path  # Set the episode_dir for correct context
    print_single_stage_menu()
    
    while True:
        choice = input(f"Enter a number (1-7) or 0: ").strip()
        if choice == "0":
            return
        if choice.isdigit() and 1 <= int(choice) <= 7:
            stage = int(choice)
            
            # If Stage 4 is selected, prompt for narrative format at the start
            narrative_format = None
            if stage == 4:
                narrative_format = get_narrative_format_choice()
                if narrative_format is None:  # User cancelled
                    return
            
            # If Stage 5 is selected, prompt for TTS provider at the start
            tts_provider = "chatterbox"  # Default
            if stage == 5:
                tts_provider = get_tts_provider_choice()
            
            # Prompt for required input file for the selected stage
            if stage == 1:
                print("[!] Stage 1 (Media Extraction) cannot be run on an existing episode.")
                return
            elif stage == 2:
                default_audio_path = os.path.join(episode_path, 'Input', 'original_audio.mp3')
                audio_path = default_audio_path if os.path.exists(default_audio_path) else input(f"Enter path to audio file (default: {default_audio_path}): ").strip() or default_audio_path
                result = processor._stage_2_transcript_generation(audio_path)
                print(f"Stage 2 complete: {result}")
            elif stage == 3:
                default_transcript_path = os.path.join(episode_path, 'Processing', 'original_audio_transcript.json')
                transcript_path = default_transcript_path if os.path.exists(default_transcript_path) else input(f"Enter path to transcript file (default: {default_transcript_path}): ").strip() or default_transcript_path
                result = processor._stage_3_content_analysis(transcript_path)
                print(f"Stage 3 complete: {result}")
            elif stage == 4:
                default_analysis_path = os.path.join(episode_path, 'Processing', 'original_audio_analysis_results.json')
                analysis_path = default_analysis_path if os.path.exists(default_analysis_path) else input(f"Enter path to analysis file (default: {default_analysis_path}): ").strip() or default_analysis_path
                # Use the narrative_format selected at the start
                result = processor._stage_4_narrative_generation(analysis_path, narrative_format)
                print(f"Stage 4 complete: {result}")
            elif stage == 5:
                default_script_path = os.path.join(episode_path, 'Output', 'Scripts', 'unified_podcast_script.json')
                script_path = default_script_path if os.path.exists(default_script_path) else input(f"Enter path to script file (default: {default_script_path}): ").strip() or default_script_path
                result = processor._stage_5_audio_generation(script_path, tts_provider)
                print(f"Stage 5 complete: {result}")
            elif stage == 6:
                default_script_path = os.path.join(episode_path, 'Output', 'Scripts', 'unified_podcast_script.json')
                script_path = default_script_path if os.path.exists(default_script_path) else input(f"Enter path to script file (default: {default_script_path}): ").strip() or default_script_path
                result = processor._stage_6_video_clipping(script_path)
                print(f"Stage 6 complete: {result}")
            elif stage == 7:
                # For stage 7, infer default paths from episode
                default_audio_results = os.path.join(episode_path, 'Output', 'Audio')
                default_clips_manifest = os.path.join(episode_path, 'Output', 'Video')
                audio_results_path = default_audio_results if os.path.exists(default_audio_results) else input(f"Enter path to audio results (dict or file) (default: {default_audio_results}): ").strip() or default_audio_results
                clips_manifest_path = default_clips_manifest if os.path.exists(default_clips_manifest) else input(f"Enter path to clips manifest (dict or file) (default: {default_clips_manifest}): ").strip() or default_clips_manifest
                import ast
                def ensure_dict(val, is_video=False):
                    if isinstance(val, dict):
                        return val
                    if isinstance(val, str) and os.path.isdir(val):
                        manifest = {'output_directory': val}
                        if is_video:
                            mp4_files = [f for f in os.listdir(val) if f.lower().endswith('.mp4')]
                            manifest['total_clips'] = len(mp4_files)
                            manifest['files'] = mp4_files
                        return manifest
                    try:
                        parsed = ast.literal_eval(val)
                        if isinstance(parsed, dict):
                            return parsed
                    except Exception:
                        pass
                    return {'output_directory': val}
                s5 = ensure_dict(audio_results_path)
                s6 = ensure_dict(clips_manifest_path, is_video=True)
                result = processor._stage_7_video_compilation(s5, s6)
                print(f"Stage 7 complete: {result}")
            return
        menu_logger.show_invalid_choice(choice, 7)

# --- Main Loop ---
def main():
    youtube_url = None
    processor = None
    content_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Content')
    
    while True:
        print_main_menu(youtube_url)
        choice = input("Enter a number (0-4): ").strip()
        
        if choice == "0":
            menu_logger.show_goodbye()
            break
            
        elif choice == "1":
            # Run FULL pipeline
            if not youtube_url:
                menu_logger.show_url_prompt()
                youtube_url = input("Enter YouTube URL: ").strip()
                if not youtube_url:
                    menu_logger.show_warning("No URL entered. Returning to main menu.")
                    continue
                else:
                    menu_logger.show_url_set_confirmation(youtube_url)
            
            # Prompt for narrative format at the very start since Stage 4 is included
            narrative_format = get_narrative_format_choice()
            if narrative_format is None:  # User cancelled
                continue
            
            # Prompt for TTS provider at the very start since Stage 5 is included
            tts_provider = get_tts_provider_choice()
                    
            if not processor:
                processor = MasterProcessorV2(verbosity=CURRENT_VERBOSITY)
                
            menu_logger.show_processing_start("FULL pipeline")
            try:
                result = processor.process_full_pipeline(youtube_url, tts_provider, narrative_format)
                menu_logger.show_info(f"Final video created: {result}", "Pipeline Complete")
            except Exception as e:
                menu_logger.show_error(f"Pipeline failed: {e}")
                
        elif choice == "2":
            if not youtube_url:
                menu_logger.show_url_prompt()
                youtube_url = input("Enter YouTube URL: ").strip()
                if not youtube_url:
                    menu_logger.show_warning("No URL entered. Returning to main menu.")
                    continue
                else:
                    menu_logger.show_url_set_confirmation(youtube_url)
                    
            if not processor:
                processor = MasterProcessorV2(verbosity=CURRENT_VERBOSITY)
            run_pipeline_end_at(processor, youtube_url)
            
        elif choice == "3":
            if not processor:
                processor = MasterProcessorV2(verbosity=CURRENT_VERBOSITY)
            run_pipeline_start_from(processor, content_dir)
            
        elif choice == "4":
            if not processor:
                processor = MasterProcessorV2(verbosity=CURRENT_VERBOSITY)
            run_pipeline_one_stage(processor, content_dir)
            
        elif choice == "9":
            menu_logger.show_url_prompt()
            youtube_url = input("Enter YouTube URL: ").strip()
            if youtube_url:
                menu_logger.show_url_set_confirmation(youtube_url)
            else:
                menu_logger.show_warning("No URL entered.")
                
        else:
            menu_logger.show_invalid_choice(choice, 4)

if __name__ == "__main__":
    main()
