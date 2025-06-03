# sharedpotato

> 📝 This file is the English version of the sharedpotato README (`README.md`).

**Experimental utility for managing asynchronously shared objects in Python**

`sharedpotato` is a Python library aimed at safely managing shared state in asynchronous programming.
**It is currently in development and also serves as a study project.** It is being published in an unfinished state to encourage feedback and transparency in its design process.

## 📦 Included Modules

As of now, this repository includes the following two modules:

### 1. `asyncvlog.py`

A lightweight logging utility for recording key events such as object creation, method invocation, and lock acquisition in asynchronous code.
Primarily intended for debugging and tracing.

Example usage:

```python
vlog_on_instance_created(self, "object created")
vlog_on_called(self, "method_name")
```

### 2. `sharedobj.py`

Provides `AsyncSharedObject`, a class for safely sharing a single value between coroutines. Key features include:

* Explicit accessor separation (Getter / Setter / Deleter) to clarify usage intent and responsibilities.
* Registration and execution of close handlers
* Lock-free accessors available in specific contexts
* Event-based synchronization for initialization (supports lazy initialization)
* Timeout control
* Automatic closing via `async with`

Internally, it integrates with `asyncvlog.py` for detailed runtime tracing.

## 🧪 Additional Notes

This library is designed and implemented using ChatGPT, and the development process is live-streamed on Twitch. If you're interested, check it out:
Twitch Channel: [https://www.twitch.tv/minoru\_jp](https://www.twitch.tv/minoru_jp)

## ⚠️ Project Status

This project is **experimental** and its API is subject to change.
Please keep in mind the following points:

* Minimal documentation
* Unit tests are incomplete or missing
* File and module structure may change significantly

The goals of open development include:

* Making the design and progress visible
* Sharing with interested developers
* Encouraging feedback and collaboration

## 📌 Planned Features

* Improved code comments and documentation
* Support for additional shared object types (e.g., sets, queues)
* Development of tests and usage examples
* Hooks and metrics for usage introspection

## 🛠️ Requirements

* Python 3.10 or later
* No external dependencies (uses standard library only)

## 📄 License

This library is released under the MIT License. See [LICENSE](./LICENSE) for details.

---

© 2025 minoru\_jp
