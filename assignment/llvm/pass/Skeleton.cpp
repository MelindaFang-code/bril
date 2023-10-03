#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
using namespace llvm;

namespace
{
    struct SkeletonPass : public PassInfoMixin<SkeletonPass>
    {
        PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM)
        {
            for (auto &F : M.functions())
            {
                for (auto &B : F)
                {
                    for (auto &I : B)
                    {
                        if (auto *op = dyn_cast<BinaryOperator>(&I))
                        {
                            IRBuilder<> builder(op);
                            Value* change;
                            Value *lhs = op->getOperand(0);
                            Value *rhs = op->getOperand(1);
                            if (op->getOpcode() == Instruction::FDiv) {
                                errs() << "finding ins " << I << " in " << F.getName() << ", changing to mult\n"; 
                                change = builder.CreateFMul(lhs, rhs);
                            }
                            else if (op->getOpcode() == Instruction::FMul)
                            {
                                errs() << "finding ins " << I << " in " << F.getName() << ", changing to add\n";
                                change = builder.CreateFAdd(lhs, rhs);
                            }
                            else if (op->getOpcode() == Instruction::FAdd)
                            {
                                errs() << "finding floating point addition in " << F.getName() << ", changing to sub\n";
                                change = builder.CreateFSub(lhs, rhs);
                            }
                            else if (op->getOpcode() == Instruction::FSub)
                            {
                                errs() << "finding floating point subtraction in " << F.getName() << ", changing to unordered & le\n";
                                change = builder.CreateFCmpULE(lhs, rhs);
                            }
                            for (auto &U : op->uses())
                            {
                                // A User is anything with operands.
                                User *user = U.getUser();
                                user->setOperand(U.getOperandNo(), change);
                            }
                        }
                    }
                }
            }
            return PreservedAnalyses::all();
        }
    };

}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo()
{
    return {
        .APIVersion = LLVM_PLUGIN_API_VERSION,
        .PluginName = "Skeleton pass",
        .PluginVersion = "v0.1",
        .RegisterPassBuilderCallbacks = [](PassBuilder &PB)
        {
            PB.registerPipelineStartEPCallback(
                [](ModulePassManager &MPM, OptimizationLevel Level)
                {
                    MPM.addPass(SkeletonPass());
                });
        }};
}
