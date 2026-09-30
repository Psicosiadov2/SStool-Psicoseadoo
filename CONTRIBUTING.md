# Contributing

Contributions are welcome through GitHub issues and pull requests.

1. Fork the repository and create a focused branch.
2. Do not commit executables, downloaded tools, virtual environments, logs,
   credentials or personal forensic data.
3. Preserve existing tool names and descriptions unless the change explicitly
   updates them.
4. Run `python -m unittest discover -s tests -v` before opening a pull request.
5. Explain what changed, why it changed and how it was tested.

New download entries should prefer permanent official release URLs and include
a SHA-256 value whenever the publisher provides one. Avoid temporary signed
links and do not add code that disables Windows security controls.
