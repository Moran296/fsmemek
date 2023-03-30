# fsmemek
Utility to generate state machine chart from my [my c++17 task fsm](https://github.com/Moran296/freertos_fsm_task)

fsmemek runs on any fsm written by my library with the following restrictions:
-   states are called STATE_*
-   events are called EVENT_*
-   Normal c/cpp conventions are used
-   functions declaration open brackets same line like: void func() {

#dependencies
-   python3
-   Any program / extension that can present plantUML files
    -   in VS code use PlantUML extension

## Usage

For fsm in file some_fsm.cpp:
python fsmemek.py some_fsm.cpp
Will create a file named some_fsm.uml

## Example

```c++
return_state class::on_event(STATE_A s_a, EVENT_B& e_a) {

   if(is_oneliner)
      return std::nullopt;

   return SOMETHING_TRENARY
                           ? STATE_A{}
                           : STATE_B{};
}

return_state class::on_event(STATE_B& s_a, EVENT_A& e_a)
{
   if (some_condition) {
      return STATE_A{};
   }

   if (some_more_ifs) {
      return STATE_A{};
   } else if (some_other_condition_number) {
      return std::nullopt;
   } else {
      return STATE_C{};
   }
}

return_state class::on_event(STATE_A s_a, EVENT_A& e_a) {
   return STATE_B{};
}

some SOME::on_event(STATE_A &, const EVENT_D &state) {
    switch (var) {
    case big:
        return STATE_C{};
    case medium:
        [[fallthrough]]
    case small:
        [[fallthrough]]
    case tiny:
        return STATE_D{};

    default:
      return std::nullopt;
    }
}
```

will generate the following uml file:

WIP

