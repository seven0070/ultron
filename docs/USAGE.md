# Using Monad-Ultron

## Starting Monad

From the USB root: **double-click `monad.bat`**.

From command line:
```cmd
monad-cli.bat            # default (banner + help)
monad-cli.bat start      # boot + status
monad-cli.bat chat       # interactive chat
monad-cli.bat doctor     # diagnose environment
```

## CLI commands

| Command | Description |
|---------|-------------|
| `monad start` | Boot Monad (config + logger + env + plugins) |
| `monad status` | Show ready state + health |
| `monad version` | Print version |
| `monad config` | Dump loaded config.yaml |
| `monad info` | Project metadata |
| `monad doctor` | Full environment diagnostic |
| `monad env` | Detailed env JSON |
| `monad plugins` | List plugins |
| `monad plugin-enable <id>` | Enable a plugin |
| `monad plugin-disable <id>` | Disable a plugin |
| `monad services` | Show DI-registered services |
| `monad models` | List registered models |
| `monad chat` | Interactive chat session |

## Chat commands (inside `monad chat`)

- `/help` — list commands
- `/clear` — clear conversation
- `/status` — session info
- `/model <id>` — switch active model
- `/exit` or `/quit` — leave chat

## Configuration

All runtime behavior is controlled by `config.yaml`. Common tweaks:

```yaml
runtime:
  default_model: "longcat2"       # or "glm5", "llama2"
  max_loaded_models: 1

chat:
  temperature: 0.7
  max_tokens: 2048

logging:
  level: "DEBUG"                  # for troubleshooting

plugins:
  auto_load: ["health", "system_info"]
```

## Adding models

Edit `models.yaml`:

```yaml
models:
  - id: "mistral7b"
    role: "reasoning"
    format: "gguf"
    filename: "mistral-7b-q4_k_m.gguf"
    url: "https://huggingface.co/…/mistral-7b-Q4_K_M.gguf"
    size_gb: 4.1
    context: 8192
    gpu_layers: -1
```

Then: `python installer/download_models.py`
