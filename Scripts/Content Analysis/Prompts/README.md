# Podcast Narrative Prompt Configurations

## Available Prompt Templates

### Default: podcast_narrative_prompt.txt
- Voice: Humorous, sarcastic, snarky (Jon Stewart style)
- Focus: General misinformation critique
- Target Duration: 25-30 minutes
- Clip Count: 4-7 clips

### Potential Variations (TODO):

#### podcast_narrative_serious.txt
- Voice: More serious, academic tone
- Focus: Educational content
- For: Sensitive topics requiring careful handling

#### podcast_narrative_comedy.txt  
- Voice: More comedic, less fact-checking focus
- Focus: Entertainment over education
- For: Lighter episodes with absurd content

#### podcast_narrative_deep_dive.txt
- Voice: Investigative journalism style
- Focus: Single topic deep analysis
- For: Complex topics requiring thorough breakdown

## Template Variables

All prompt templates support these variables:
- `{episode_title}`: Full episode title
- `{analysis_json}`: Complete analysis data as JSON string
- `{guest_name}`: Guest name (if available)
- `{episode_date}`: Episode date (if available)
- `{custom_instructions}`: Additional context or instructions

## Usage in Code

```python
# Load specific prompt template
prompt_loader = PromptLoader("Scripts/Content Analysis/Prompts/")
prompt = prompt_loader.load_template("podcast_narrative_prompt.txt")

# Fill template variables
filled_prompt = prompt.format(
    episode_title="Joe Rogan Experience 2325 - Aaron Rodgers",
    analysis_json=json.dumps(analysis_data, indent=2)
)
```
