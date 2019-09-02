# Welcome to ha-fsm

Most programmers are used to finate-state-machines to control the behavior of things. (https://en.wikipedia.org/wiki/Finite-state_machine)

It is built in python using the appdaemon package. You need to be prepared to write python to use this package, but most of the code can be copy-pasted. So do not be intimidated even if you are not a ninja at programming.
This package allows you to:
- Add machines
- Add states to each machine
- Add transisitons between the states
- Add conditions to tell when transitions are valid

A condition can be based on time, current state of entities in Home Assistant, and anything else imported into python
A transition can be a single condition, or multiple of them (AND'ed)
If there should multiple ways to go from one state to another, just add several transitions (OR'ed)

But something should also happen, or else it would be meaningless.
So when a state is enter or exited, it is possible to execute one or several python programs. Same when a transition is used. Here you can easily alter entities from Home Assistant, call services, or anything else supported by appdaemon API. If this is not enough, just import your favorite python library and do it your own way.

Some real-life signals are not always stable and trustworthy at every moment in time. To support this, it is possible to request signals to be stable for a certain amount of time before they are considered to have changed.

# Installation
Install home assistant (https://www.home-assistant.io/getting-started/)
Install appdaemon (https://appdaemon.readthedocs.io/en/latest/INSTALL.html)
Download this package and put fsm.py file in appdaemon apps folder

# Usage
Add a new app in appdaemon (see "Configuring a Test App" https://appdaemon.readthedocs.io/en/latest/CONFIGURE.html#initial-setup) and point this app to a ha-fsm component



# Full-blown example of simple alarm state machine

    class Fsm_alarm(hass.Hass):
      def initialize(self):
        Fsm_alarm = Fsm(self, id='Fsm_alarm', entity='input_text.fsm_alarm_status', states=[
          State(id='Alarm armed', enter_programs=[self.siren_off], transitions=[
            Transition(next='Alarm triggered', conditions=[
              Condition(entity='sensor.detector1', operand='on'),
              Condition(entity='sensor.detector2', operand='on')
            ]),
            Transition(next='Alarm disarmed', conditions=[
              Condition(entity='alarm_panel.state', operand='home')
            ])
          ]),
          State(id='Alarm triggered', enter_programs=[self.siren_on], transitions=[
            Transition(next='Alarm disarmed', conditions=[
              Condition(entity='alarm_panel.state', operand='home')
            ])
          ]),
          State(id='Alarm disarmed', enter_programs=[self.siren_off], transitions=[
            Transition(next='Alarm armed', conditions=[
              Condition(entity='alarm_panel.state', operand='away')
            ])
          ])
        ])
    
      class siren_off:
        def program(self):
          self.hass.log('Siren OFF..', level='INFO')
          # ... add code to actually turn the siren off
    
      class siren_on:
        def program(self):
          self.hass.log('Siren ON..', level='INFO')
          # ... add code to actually turn the siren on

# API
The entire definition of the machine, including states, transitions and programs, are done in python

## FSM
  **fsm**(hass, id, **states**, entity, health_entity):
- hass is a reference to a hassapi class, usually  'self' 
- id is optional but useful for debugging
- states is a required list of; State objects
- entity is an optional hass entity where the current state is published
- health_entity is an optional  hass entity where the health of this fsm is made public

  **log_graph_link**()
Print a link to an external site producing a graphical view of the machine. **Note** if the graph string is large the direct link will not work. Instead, copy/paste the text directly at the external site and it will work

## State
**state**(id, name, **transitions**, enter_programs, exit_programs):
 - id is optional but useful for debugging
 - name is the name of this state. If set to None, id will be used instead
 - transitions is a list of; Transition objects
 - enter_programs is an optional list of; objects containing a 'program' function, or a python string to be executed
 - exit_programs is an optional list of; objects containing a 'program' function, or a python string to be executed

## Transition
**transition**(id, next, **conditions**, programs):
 - id is optional but useful for debugging
 - next is the id of the next state if all conditions are found true
 - conditions is a list of; Condition objects
 - programs is an optional object containing a list of program functions

### Examples:
        Transition(next='No activity', conditions=[
          Condition(entity='sensor.alarm_basement', operand='off'),
          Condition(entity='sensor.alarm_garage', operand='off'),
        ])


## Condition
**condition**(id, entity, attribute, operator, operand, stability_time, timeout_time, timeout_entity, years, months, weeks, days, weekdays, hours, minutes):
 - id is optional but useful for debugging
 - entity is an optional hass entity which can be tested by the operator
 - attribute is an optional hass attribute for entity which can be tested by the operator
 - operator is required if entity is used, and is an object with a check function
 - stability_time is optional but only used if entity is used, and sets a minimum time operator must be true before this condition evaluates as true
 - timeout_time is optional and a minimum time before this condition evaluates as true
 - timeout_entity is optional and name of entity containing a minimum time before this condition evaluates as true
 - years, months, weeks, days, weekdays, hours, minutes are optional lists of allowed times. If more than one is set, consider an implicit "and" between them

### Examples:
 1. Wait a while:

    Condition(timeout_time=**15*60**)
 
 2. Wait a while (same as above), but time the value is taken from hass entity
 
    Condition(timeout_entity="**input_number.user_timeout**")
  
 4. Check if the user changes an entity:

    Condition(entity='**input_select.light_mode**', operand='**Auto**')  # Operator is implicitly set to '**EQ**' - see below

 3. Check if an attribute of an entity is above a certain threshold

    Condition(entity='**sun.sun**', attribute='**elevation**', operator=**GE**, operand=**30**)
It is easy to add new custom operators if the need arises, but these are the built-in operators:
- EQ - Equal (This is the implicit choice if no operator is specified)
- NE - Not equal
- GT - Greater than
- GE - Greater or equal than
- LT - Less than
- LE - Less or equal than

 4. Check if month is april to september, and time is between 10.xx and 21.xx (effectively 10.00:00 and 21.59:59):

    Condition(**months=range(4,10)**, **hours=range(10,22)**)

 5. Check only if a signal is stable for a certain period (in secods)

    Condition(entity='input_boolean.pool_water_low', operand='on', **stability_time=5**)

All these can be combined in arbitrary combinations to derive complex conditions like:

    Condition(**timeout_entity="input_number.user_timeout"**, **months=range(4,10)**, **hours=range(10,22)**, **stability_time=5**)

This would (in plain English) mean: Wait the time specified in **"input_number.user_timeout"**, it must be stable for at least **5** seconds, in **april** through **september**, between **10.00:00** and **21.59:59**.

# Known issues
- If several transition have the same timeout-time, it is arbitrary which first becomes true
- If a entity change of state makes several transitions become true, it is arbitrary which transition is activated
- There is no protection against bad code, and it relatively easy to create infinite loops and similar. If it happens, kill appdaemon and fix your configuration problem


