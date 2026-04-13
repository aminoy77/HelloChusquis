# HelloChusquis 🧠✨

**HelloChusquis** is an advanced, self-improving AI terminal agent built in Python. Designed for developers and power-users, it seamlessly integrates with your terminal to automate complex tasks, manage files, execute code, and even build its own tools on demand.

## 🚀 Features & Capabilities

HelloChusquis is more than just a terminal agent; it's a dynamic, evolving system:

*   **Intelligent Task Automation**: Execute terminal commands, manage files (read, write, create, delete), and run Python code directly within your workspace.
*   **Multi-Provider AI Orchestration**: Supports a wide array of AI providers (OpenRouter, Ollama Cloud, Anthropic, OpenAI, Gemini, Groq, xAI, Perplexity, Qwen, MiniMax, Mistral, DeepSeek, Cohere, Together AI, Fireworks, Novita, and more) with automatic fallback and intelligent retry mechanisms for enhanced reliability.
*   **Self-Building Agent (`core/builder.py`)**: A groundbreaking feature that allows HelloChusquis to:
    *   **Research APIs**: Automatically investigate new APIs and functionalities on the web.
    *   **Generate Plugins**: Write new Python plugins from scratch, adhering to the official HelloChusquis plugin standard.
    *   **Self-Validate & Self-Correct**: Test newly generated plugins in a sandbox environment and iteratively fix errors.
    *   **Suggest Contributions**: Provide clear instructions for contributing new, self-built plugins to the official repository via Pull Requests.
*   **Robust Error Handling**: Features `chat_with_retry` for resilient AI interactions and clean, user-friendly error messages (e.g., `⚠ Step X failed, skipping...`) to maintain workflow continuity.
*   **Rich Plugin Ecosystem**: Access to the [HelloChusquis-Plugins](https://github.com/aminoy77/HelloChusquis-plugins) repository, offering a vast collection of over 80 specialized tools, including:
    *   **`browser`**: Advanced web navigation, search (via Brave Search), content extraction, and screenshots.
    *   **`stocks`**: Real-time stock data, historical analysis, and financial insights powered by `yfinance`.
    *   And many more for productivity, communication, development, and entertainment.
*   **Persistent Memory**: Maintains conversation history and context across sessions, ensuring a seamless user experience.

## ⚡ Quick Start

Get HelloChusquis up and running in minutes:

### 📥 Installation

Choose your preferred method:

#### 📦 Via `pip` (Recommended)
```bash
pip install hellochusquis
```

#### 🌐 Via `curl` (One-click)
```bash
curl -sSL https://raw.githubusercontent.com/aminoy77/HelloChusquis/main/install.sh | bash
```

#### 💻 Via `git clone`
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/aminoy77/HelloChusquis.git
    cd HelloChusquis
    ```
2.  **Install dependencies**:
    ```bash
    pip install -e .
    ```
    *(Ensure you have Python 3.9+ installed. `pip` will handle other requirements.)*

#### ⬇️ Download ZIP
1.  Download the latest release ZIP from [GitHub](https://github.com/aminoy77/HelloChusquis/releases).
2.  Unzip the file and navigate into the directory.
3.  Install dependencies: `pip install -e .`

### ▶️ Run the Agent

Simply execute from your terminal:

```bash
hellochusquis
```

*The first run will guide you through configuring your AI providers. It's highly recommended to add at least two providers to enable the automatic fallback mechanism.* 

### 🔌 Plugin Management

Extend HelloChusquis's capabilities by installing and uninstalling plugins from the official repository:

*   **Install a plugin**:
    ```bash
    hellochusquis install <plugin_name>
    ```
    *Example: `hellochusquis install browser`*

*   **Uninstall a plugin**:
    ```bash
    hellochusquis uninstall <plugin_name>
    ```
    *Example: `hellochusquis uninstall browser`*

## ⚙️ Core Commands

HelloChusquis offers several commands to enhance your interaction:

| Command                  | Description                                                                                               |
| :----------------------- | :-------------------------------------------------------------------------------------------------------- |
| `hellochusquis`          | Starts the agent in terminal chat mode.                                                                   |
| `hellochusquis web`      | Launches a web-based interface for interacting with the agent in your browser.                            |
| `hellochusquis learn`    | Initiates a learning session where the agent can be taught new skills or workflows.                       |
| `/help`                  | Displays a list of available commands and their descriptions.                                             |
| `/plan <task>`           | Forces the agent into planning mode to break down and execute complex tasks.                              |
| `/status`                | Shows the status of configured AI providers and other system information.                                 |
| `/clear`                 | Clears the current conversation history.                                                                  |
| `exit`                   | Exits the agent and saves the session memory.                                                             |
| `👍` or `+`              | Provides positive feedback to the agent, helping it learn and improve.                                     |
| `👎` or `-`              | Provides negative feedback, indicating an area for improvement.                                           |

## 🤝 Contributing

We welcome contributions from the community! Whether it's a new plugin, a bug fix, or an enhancement to the core agent, your input is valuable.

1.  **Fork** the project.
2.  Create a new branch for your feature or fix: `git checkout -b feature/your-feature-name`.
3.  **Commit** your changes: `git commit -m 'feat: Add your feature'`.
4.  Push to the branch: `git push origin feature/your-feature-name`.
5.  Open a **Pull Request**.

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for more details.

---
*Developed with ❤️ by aminoy77 and the HelloChusquis community.*
