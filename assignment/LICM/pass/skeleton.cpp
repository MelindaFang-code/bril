
// https://github.com/abhandaru/cs745-llvm-src/blob/master/ClassicalDataflow/loop-invariant-code-motion.cpp
// http://www.few.vu.nl/~lsc300/LLVM/doxygen/LoopInfo_8cpp_source.html#l00070
// https://aktemur.github.io/cs544/assignment_opt.html
// namespace
// {
//     struct LicmPass : public PassInfoMixin<LicmPass>
//     {
//         void getAnalysisUsage(AnalysisUsage &AU) const
//         {
//             AU.setPreservesCFG();
//             AU.addRequired<LoopInfoWrapperPass>();
//         }
//         bool isLoopInvariant(Loop* L, Instruction *I)
//         {
//             // if instructions are binary operator, shift, select, cast, getelementptr
//             if (I->isBinaryOp() || I->isShift() || I->isCast() || 
//                 isa<GetElementPtrInst>(I))
//             {
//                 for (auto operand = I->operands().begin(); operand != I->operands().end(); ++operand){
//                     if (Instruction *Ins = dyn_cast<Instruction>(operand))
//                     {
//                         if (L->contains(Ins))
//                             return false;
//                     }
//                 }
//                 return true;
//             } 
//             return false;
//         }

//         bool safeToHoist(Loop* L, Instruction* I)
//         {
//             if (!isSafeToSpeculativelyExecute(I))
//                 return false;

//             // instruction is in the header block for the loop
//             if (I->getParent() == L->getHeader())
//                 return true;
//             // The basic block dominates all exit blocks for the loop. 
//             // Use dominator tree to check for dominance.
//             // auto exitBlocks = L->getExitBlocks();
//             // for (unsigned i = 0, e = exitBlocks.size(); i != e; ++i)
//             //     if (!DT->dominates(I.getParent(), ExitBlocks[i]))
//             //         return false;
//         }

//         bool LICM(Loop *L)
//         {
//             BasicBlock* preheader = L->getLoopPreheader();
//             if (!preheader) return false;
//             auto InsertPt = preheader->getTerminator();
//             std::vector<BasicBlock::iterator> ins_move;
//             // Each Loop object has a preheader block for the loop .
//             for (auto block = L->block_begin(), end = L->block_end(); block != end; ++block){
//                 for (BasicBlock::iterator instr = (*block)->begin(), be = (*block)->end();
//                      instr != be; ++instr)
//                 {
//                     Instruction *V = &(*instr);
//                     if (isLoopInvariant(L, V) && safeToHoist(L, V)){
//                         V->moveBefore(InsertPt);
//                         bool Changed = true;
//                     }
//                 }
                
//             }
//         }

//         PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM)
//         {
//             auto &FAM = AM.getResult<FunctionAnalysisManagerModuleProxy>(M).getManager();
//             for (auto &F : M.functions())
//             {
//                 LoopInfo &LI = FAM.getResult<llvm::LoopAnalysis>(F);
//                 for (auto L : LI) {
//                     LICM(L);
//                 }
//                 for (auto &B : F)
//                     {
//                         for (auto &I : B)
//                         {
//                             if (auto *op = dyn_cast<BinaryOperator>(&I))
//                             {
//                                 IRBuilder<> builder(op);
//                                 Value *change;
//                                 Value *lhs = op->getOperand(0);
//                                 Value *rhs = op->getOperand(1);
//                                 if (op->getOpcode() == Instruction::FDiv)
//                                 {
//                                     errs() << "finding ins " << I << " in " << F.getName() << ", changing to mult\n";
//                                     change = builder.CreateFMul(lhs, rhs);
//                                 }
                                
//                                 for (auto &U : op->uses())
//                                 {
//                                     // A User is anything with operands.
//                                     User *user = U.getUser();
//                                     user->setOperand(U.getOperandNo(), change);
//                                 }
//                             }
//                         }
//                     }
//                 }
//             return PreservedAnalyses::all();
//         }

//         private:
//             // LoopInfo *LI;      // Current LoopInfo
//             DominatorTree *DT; // Dominator Tree for the current Loop.
//             // State that is updated as we process loops.
//             bool Changed;          // Set to true when we change anything.
//             BasicBlock *Preheader; // The preheader block of the current loop...
//             Loop *CurLoop;         // The current loop we are working on...
//     };

// }

// extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
// llvmGetPassPluginInfo()
// {
//     return {
//         .APIVersion = LLVM_PLUGIN_API_VERSION,
//         .PluginName = "licm pass",
//         .PluginVersion = "v0.1",
//         .RegisterPassBuilderCallbacks = [](PassBuilder &PB)
//         {
//             PB.registerPipelineStartEPCallback(
//                 [](ModulePassManager &MPM, OptimizationLevel Level)
//                 {
//                     MPM.addPass(LicmPass());
//                 });
//         }};
// }

#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Analysis/ValueTracking.h"
#include "llvm/IR/Dominators.h"
#include "llvm/Analysis/PostDominators.h"

using namespace llvm;

namespace
{

    struct SkeletonPass : public PassInfoMixin<SkeletonPass>
    {

        std::set<Value> getLoopInvariants(Loop *L)
        {
            std::set<Value> loopInvariants;
            int loopInvariantsSize = 0;
            do
            {
                loopInvariantsSize = loopInvariants.size();
                for (auto &BB : L->blocks())
                {
                    for (auto &I : *BB)
                    {
                        bool isLoopInvariant = true;
                        for (int i = 0; i < I.getNumOperands(); i++)
                        {
                            Value *operand = I.getOperand(i);
                            if (L->contains(operand) && loopInvariants.count(*operand))
                            {
                                isLoopInvariant = false;
                                break;
                            }
                        }
                        if (isLoopInvariant)
                        {
                            loopInvariants.insert(I);
                        }
                    }
                }
            } while (loopInvariants.size() > loopInvariantsSize);
            return loopInvariants;
        }

        bool checkLoopInvariant(std::set<Value> &Invariants, Instruction *I)
        {
            // if instructions are binary operator, shift, select, cast, getelementptr
            // if (I->isBinaryOp() || I->isShift() || I->isCast() ||
            //     isa<GetElementPtrInst>(I))
            // {
            for (auto operand = I->operands().begin(); operand != I->operands().end(); ++operand)
            {
                if (Value *Ins = dyn_cast<Value>(operand))
                {
                    if (!Invariants.count(*Ins))
                        return false;
                }
            }
            return true;
            // }
            // return false;
        }

        bool safeToHoist(Loop *L, Instruction *I, DominatorTree *DT)
        {
            // check side effects
            // if (!isSafeToSpeculativelyExecute(I))
            //     return false;

            for (auto U : I->users())
            {
                if (auto user = dyn_cast<Instruction>(U))
                {
                    if (!DT->dominates(I->getParent(), user->getParent()))
                    {
                        errs() << "not dominate use!\n";
                        return false;
                    };
                }
            }
            // The basic block dominates all exit blocks for the loop.
            // Use dominator tree to check for dominance.
            SmallVector<BasicBlock *> ExitBlocks = SmallVector<BasicBlock *>();
            L->getExitingBlocks(ExitBlocks);
            for (unsigned i = 0, e = ExitBlocks.size(); i != e; ++i)
                if (!DT->dominates(I->getParent(), ExitBlocks[i]))
                {
                    for (BasicBlock::iterator instr = ExitBlocks[i]->begin(), be = ExitBlocks[i]->end(); instr != be; ++instr)
                    {
                        Instruction *V = &(*instr);
                        errs() << *V << "\n";
                    }
                    errs() << "not dominate exit!\n";
                    return false;
                }
            return true;
        }

        bool LICM(Loop *L, DominatorTree *DT)
        {
            errs() << "enter LICM\n";
            bool Changed = false;
            BasicBlock *preheader = L->getLoopPreheader();
            if (!preheader)
                return false;
            auto InsertPt = preheader->getTerminator();
            std::vector<BasicBlock::iterator> ins_move;
            // Each Loop object has a preheader block for the loop .
            std::set<Value> loopInvariants = getLoopInvariants(L);
            for (auto block = L->block_begin(), end = L->block_end(); block != end; ++block)
            {
                for (BasicBlock::iterator instr = (*block)->begin(), be = (*block)->end();
                     instr != be; ++instr)
                {
                    Instruction *V = &(*instr);
                    errs() << "Instruction: " << *V << "\n";
                    errs() << L->isLoopInvariant(V) << " " << safeToHoist(L, V, DT) << "\n";
                    // if (loopInvariants.count(L) != loopInvariants.end() && safeToHoist(L, V, DT))
                    if (checkLoopInvariant(loopInvariants, V) && safeToHoist(L, V, DT))
                    {
                        V->moveBefore(InsertPt);
                        errs() << "Should move instruction" << V << "\n";
                        Changed = true;
                    }
                }
            }
            return Changed;
        }

        PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM)
        {
            auto &FAM = AM.getResult<FunctionAnalysisManagerModuleProxy>(M).getManager();
            for (auto &F : M)
            {
                errs() << "I saw a function called " << F.getName() << "!\n";
                auto &LI = FAM.getResult<LoopAnalysis>(F);
                DominatorTree *DT = new DominatorTree(F);
                // print the loops first
                // for (auto &L : LI) {
                //     errs() << "Loop:\n";
                //     for (auto &BB : L->blocks()) {
                //         for (auto &I : *BB) {
                //             errs() << "Instruction: " << I << "\n";
                //         }
                //     }
                // }
                for (auto L : LI)
                {
                    LICM(L, DT);
                }
            }
            return PreservedAnalyses::all();
        };
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