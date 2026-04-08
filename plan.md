but how will i get the pointer addresses at runtime? i need to load them from whatever is at the current stack pointer offset? and i store them at the stack pointer offset as well at CALL time? so load obviously needs to happen in the fn block in lowering. the call time probably needs to instead of @src/compiler/lowering.py:65-69 doing this with the regs, storing in whatever addressed by the stack pointer, increment it. and then ret needs to also decrement the stack pointer by the correct amount of args, which i can do by traversing the code block upwards until i find the function declaration as i can parse function params from that.

CALL time:
store the params relative to the current sp, decrement sp by params (lowlevel call handles the other 1)

FN time: 
extract the params relative to the current sp

RET time:
increment sp by number of params (lowlevel ret handles the other 1)

this solves the problem of function params getting fucked

---

then you need to solve the problem that is function internal register defs not being consistent 

generally:
- model the call / rets as jumps / codeblock changes etc like they actually are
# done

- model the call as an instruction that will actually define things. this is instruction level.

so how about this. for every spilled register, i reserve a memory slot for in in stack memory. then in the prelude, i decrement the sp by how ever many memory slots i have. then, when i detect a spill, r6 is reserved and used as a temp for loading and storing the temp. so i replace all defs of rSPILL with store r6, reserved memory address and all uses wilth load r6, reserved addr