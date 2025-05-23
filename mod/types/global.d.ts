type LogicBuild = typeof LogicBlock.prototype.LogicBuild.prototype;

namespace Packages {
    namespace mindustry {
        namespace logic {
            interface LExecutor {
                public optionalVar(name: string): Packages.mindustry.logic.LVar | null;
            }
        }
    }
}

// this is so cursed

function Mlogv32Memory(method: "getProcessor"): Mlogv32Memory_getProcessor;
function Mlogv32Memory(method: "forEach"): Mlogv32Memory_forEach;
function Mlogv32Memory(method: "flash"): Mlogv32Memory_flash;
function Mlogv32Memory(method: "dump"): Mlogv32Memory_dump;

type Mlogv32Memory_getProcessor = (address: number) => LogicBuild;

type Mlogv32Memory_forEach = (
    callback: (word: LVar, address: number) => boolean,
    onProgress: (bytes: number) => any,
    onFinish: (bytes: number) => any,
    onError: (e: Error) => any,
    startAddress: number
) => void;

type Mlogv32Memory_flash = (
    file: Fi,
    onProgress: (progress: number, total: number) => any,
    onFinish: (bytes: number) => any,
    onError: (e: Error) => any
) => void;

type Mlogv32Memory_dump = (
    file: Fi,
    onProgress: (progress: number, total: number) => any,
    onFinish: (bytes: number) => any,
    onError: (e: Error) => any
) => void;
