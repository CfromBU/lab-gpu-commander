# Lab GPU VS Code Extension

## Dev Run

```
cd vscode
npm install
npm run compile
```

Press `F5` in VS Code to launch Extension Development Host, then right-click a file and choose "Submit to GPU Queue".

## Package (VSIX)

```
cd vscode
npm install
npm run compile
npx vsce package
```

This produces a `.vsix` file in `vscode/`.

## Install VSIX

```
code --install-extension lab-gpu-0.0.1.vsix
```

## Optional Workspace Config

Create `.labgpu_config.json` in your workspace root:

```
{
  "default_mem": "10G"
}
```
