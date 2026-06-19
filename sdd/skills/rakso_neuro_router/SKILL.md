# Skill: Neuro-Router v1.0 (Layer 9 of the RAKSO Canonical Architecture)

## Overview
The Neuro-Router module is the Layer 9 of the RAKSO Canonical Architecture. It acts as an agnostic routing engine designed to take validated strategic output (copy + funnel metadata) and map them to platform-specific JSON payloads.

This system guarantees **zero content alteration** to ensure the psychological integrity of the copy approved by "The Bridge" is preserved when mapping to TTS engine payloads, image generators, ad network formats, etc.

## Architecture & Design
To avoid vendor lock-in, the Neuro-Router operates via an abstract plugin architecture:
- `StrategyOutput`: Standard input model containing psychological copy content and neurofunnel metadata.
- `TargetAdapter`: Abstract base class that defines the plugin interface (`transform`).
- `AudioAdapter`, `VisualAdapter`, `DistributionAdapter`: Sub-interfaces defining domains for sound, visuals, and publishing.
- `MockAudioAdapter`, `MockVisualAdapter`, `MockDistributionAdapter`: Default mock adapters demonstrating direct transform mappings.

```
+----------------+       +---------------+
| StrategyOutput | ----> | Neuro-Router  |
+----------------+       +---------------+
                                 |
                                 v
                       +-------------------+
                       |   TargetAdapter   |
                       | (transform method)|
                       +-------------------+
                                 |
             +-------------------+-------------------+
             |                   |                   |
             v                   v                   v
      [AudioAdapter]      [VisualAdapter]   [DistributionAdapter]
             |                   |                   |
             v                   v                   v
     MockAudioAdapter    MockVisualAdapter  MockDistributionAdapter
             or                  or                  or
       Custom TTS          Custom Image        Custom Network
```

## Zero-Alteration Integrity Protection
To prevent AI hallucinations, message truncation, or unauthorized hype-injection, the router executes a recursive payload scanning validation (`validate_no_alteration`) checking:
1. The exact original text is embedded verbatim somewhere within the resulting dictionary/JSON values.
2. Any other text fields containing text that overlap significantly (overlap ratio > 50% of the original word set) but are not identical to the original content will trigger an `Integrity Violation` ValueError.

## Subclassing & Custom Adapters
Developers can plug in custom platforms (e.g., ElevenLabs, local Bark models, Stable Diffusion, or custom webhooks) by subclassing the corresponding domain adapter and implementing `transform(self, strategy_output: StrategyOutput) -> Dict[str, Any]`.

### Example: Custom Audio Adapter
```python
from rakso_neuro_router.adapters.audio import AudioAdapter
from rakso_neuro_router.models import StrategyOutput
from typing import Dict, Any

class MyCustomOpenSourceAudioAdapter(AudioAdapter):
    local_model_path: str
    sample_rate: int = 22050
    voice_preset: str = "v2/en_speaker_0"
    
    def transform(self, strategy_output: StrategyOutput) -> Dict[str, Any]:
        return {
            "model_path": self.local_model_path,
            "settings": {
                "sample_rate": self.sample_rate,
                "voice_preset": self.voice_preset
            },
            "tts_payload": {
                "text": strategy_output.content,
                "metadata": {
                    "stage": strategy_output.neurofunnel_map.funnel_stage.value
                }
            }
        }
```

## Running Tests
Run tests using:
```bash
pytest sdd/skills/rakso_neuro_router/tests/ -v --cov=rakso_neuro_router
```
