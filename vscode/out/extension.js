"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
const STATUS_POLL_MS = 10000;
const LAST_MEM_KEY = "labgpu.lastMem";
let lastOoms = 0;
function runCli(command, cb) {
    (0, child_process_1.exec)(command, { shell: "/bin/bash" }, (err, stdout, stderr) => {
        cb(err, stdout, stderr);
    });
}
function activate(context) {
    const output = vscode.window.createOutputChannel("Lab GPU");
    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBar.text = "GPU: loading...";
    statusBar.show();
    const submitCmd = vscode.commands.registerCommand("labgpu.submit", async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage("No active editor to submit.");
            return;
        }
        const filePath = editor.document.fileName;
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        let defaultMem = context.globalState.get(LAST_MEM_KEY) || "10G";
        if (workspaceFolder) {
            const configUri = vscode.Uri.joinPath(vscode.Uri.file(workspaceFolder), ".labgpu_config.json");
            try {
                const bytes = await vscode.workspace.fs.readFile(configUri);
                const parsed = JSON.parse(Buffer.from(bytes).toString("utf8"));
                if (parsed.default_mem) {
                    defaultMem = parsed.default_mem;
                }
            }
            catch {
                // ignore if config missing
            }
        }
        const mem = await vscode.window.showInputBox({
            prompt: "GPU memory requirement (e.g. 10G)",
            value: defaultMem,
        });
        if (!mem) {
            return;
        }
        context.globalState.update(LAST_MEM_KEY, mem);
        const command = `lab-gpu submit --mem ${mem} "python ${filePath}"`;
        output.appendLine(`$ ${command}`);
        output.show(true);
        runCli(command, (err, stdout, stderr) => {
            if (stdout)
                output.appendLine(stdout.trim());
            if (stderr)
                output.appendLine(stderr.trim());
            if (err) {
                vscode.window.showErrorMessage(`Submit failed: ${err.message}`);
            }
            else {
                vscode.window.showInformationMessage("Task submitted to GPU queue.");
            }
        });
    });
    const statusTimer = setInterval(() => {
        runCli("lab-gpu status --json", (err, stdout, stderr) => {
            if (err || stderr) {
                statusBar.text = "GPU: unavailable";
                return;
            }
            try {
                const parsed = JSON.parse(stdout);
                statusBar.text = `GPU: ${parsed.busy ?? 0}/${parsed.total ?? 0} Busy | My Tasks: ${parsed.my_running ?? 0}`;
                if (typeof parsed.ooms === "number" && parsed.ooms > lastOoms) {
                    lastOoms = parsed.ooms;
                    if (parsed.last_oom_task) {
                        vscode.window.showWarningMessage(`Task #${parsed.last_oom_task} Failed (OOM). Auto-retrying with more memory...`);
                    }
                }
            }
            catch {
                statusBar.text = "GPU: parse error";
            }
        });
    }, STATUS_POLL_MS);
    statusBar.command = "labgpu.showTasks";
    const showTasks = vscode.commands.registerCommand("labgpu.showTasks", async () => {
        runCli("lab-gpu status --json", (err, stdout) => {
            if (err) {
                vscode.window.showErrorMessage("Failed to fetch tasks.");
                return;
            }
            try {
                const parsed = JSON.parse(stdout);
                const running = parsed.running || [];
                const items = running.map((t) => ({ label: t.label, description: `Task #${t.id}`, id: t.id }));
                vscode.window.showQuickPick(items, { placeHolder: "Running tasks" }).then((pick) => {
                    if (!pick)
                        return;
                    const logCmd = `lab-gpu logs ${pick.id} -f`;
                    output.appendLine(`$ ${logCmd}`);
                    output.show(true);
                    runCli(logCmd, (_err, out, _stderr) => {
                        if (out)
                            output.appendLine(out.trim());
                    });
                });
            }
            catch {
                vscode.window.showErrorMessage("Failed to parse tasks.");
            }
        });
    });
    context.subscriptions.push(submitCmd, showTasks, statusBar);
    context.subscriptions.push({ dispose: () => clearInterval(statusTimer) });
}
function deactivate() { }
//# sourceMappingURL=extension.js.map