PS C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber> & C:/Users/nfaug/AppData/Local/Programs/Python/Python312/python.exe "c:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Code/run_pipeline_menu.py"


╭──────────────────────────────────────────────── 🎬 YouTube Processing Pipeline ────────────────────────────────────────────────╮
│                                                                                                                                │
│  1  Run FULL pipeline (all 7 stages)                                                                                           │
│  2  Run pipeline (END at selected stage)                                                                                       │
│  3  Start pipeline from specific stage                                                                                         │
│  4  Run ONE STAGE ONLY                                                                                                         │
│                                                                                                                                │
│  0  Exit                                                                                                                       │
│                                                                                                                                │
│  Current YouTube URL: not set                                                                                                  │
│                                                                                                                                │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Enter a number (0-4): 3
MasterProcessorV2 initialized - Session: session_20250705_164748
Configuration loaded from: c:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Code\Config\default_config.yaml
Content directory: c:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content


  1      Joe_Rogan_Experience - Joe Rogan Experience #2308 - Jordan Peterson
  2      Joe_Rogan_Experience - Joe Rogan Experience #2325 - Aaron Rodgers
  3      Joe_Rogan_Experience - Joe Rogan Experience #2335 - Dr. Mary Talley Bowden
  4      Joe_Rogan_Experience - Joe Rogan Experience #2340 - Charley Crockett
  5      Joe_Rogan_Experience - Joe Rogan Experience #2341 - Bernie Sanders
  6      Tucker_Carlson - RFK_Jr_Provides_an_Update_on_His_Mission_to_End_Skyrocketing...
  7      Tucker_Carlson - Tucker_Carlson_RFK_Jr
       
  0      Back to main menu


╭───────────────────────────────────────────────────── 📺 Episode Selection ─────────────────────────────────────────────────────╮
│ Select an episode from the list above                                                                                          │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Enter a number (1-7) or 0: 7


╭─────────────────────────────────────────────────────── Episode Selected ───────────────────────────────────────────────────────╮
│ ℹ️  Selected episode: Tucker_Carlson\Tucker_Carlson_RFK_Jr                                                                      
│
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯


╭──────────────────────────────────────────────────── 🚀 Select START Stage ─────────────────────────────────────────────────────╮
│                                                                                                                                │
│  1  Media Extraction                                                                                                           │
│  2  Transcript Generation                                                                                                      │
│  3  Content Analysis                                                                                                           │
│  4  Narrative Generation                                                                                                       │
│  5  Audio Generation                                                                                                           │
│  6  Video Clipping                                                                                                             │
│  7  Video Compilation                                                                                                          │
│                                                                                                                                │
│  0  Back to main menu                                                                                                          │
│                                                                                                                                │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Enter a number (1-7) or 0: 3

🎤 TTS Provider Selection
1. Chatterbox TTS (Free)
2. ElevenLabs TTS (Paid - Higher Quality)
Select TTS provider (1-2): 1
╭────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                  🧠 Stage 3: Content Analysis                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Processing transcript: original_audio_transcript.json (280.3 KB)
⠦ Initializing Gemini AI
Uploading transcript to Gemini AI...
⠏ Uploading transcript data
Loaded analysis rules: 34.1 KB
Starting AI content analysis...
⠼ Analyzing content with Gemini AI (this may take a few minutes)
⠋ Saving analysis results
✅ Content analysis completed successfully!
• Output file: original_audio_analysis_results.json
• Analysis size: 48.5 KB
Stage 3 complete: c:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Tucker_Carlson\Tucker_Carlson_RFK_Jr\Processing\original_audio_analysis_results.json


╭────────────────────────────────────────────────── 📝 Select Narrative Format ──────────────────────────────────────────────────╮
│                                                                                                                                │
│  1  Narrative with Opening Hook (tts_podcast_narrative_prompt.txt)                                                             │
│  2  Narrative WITHOUT Opening Hook (tts_podcast_narrative_prompt_WITHOUT_HOOK.txt)                                             │
│                                                                                                                                │
│  0  Cancel                                                                                                                     │
│                                                                                                                                │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Enter a number (0-2):