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
