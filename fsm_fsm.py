
# Finite state machine class for AppDaemon (Home Assistant).

from urllib.parse import quote
from datetime import datetime, timedelta

debug = False

class Fsm:
  # Finite state machine implementation for AppDaemon and Home Assistant

  # Helper function to simplify print and log messages
  def prefix(self):
    return '{} : '.format(self.id)
  
  def __init__(self, hass, id='', states=None, entity=None):
    # - id is optional but useful for debugging
    # - states is a required list of; State objects
    # - entity is an optional hass entity where the current state is published
    
    self.hass = hass
    self.id = id
    self.states = states
    self.entity = entity

    self.initialize2({})
        

  def initialize2(self, kwargs):
    self.state = None
    
    self.watchdog_handle = None
    self.feed()

    self.states_dict = {}
    for state in self.states:
      #      self.hass.log('{}State : {}'.format(self.prefix(), state.id), level='INFO')
      self.states_dict[state.id] = state
    
    if self.entity:
      # Try loading the state from Home Assistant.
      entity_state = self.hass.get_state(self.entity)
      assert entity_state, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
      
      if entity_state in {state.id for key,state in self.states_dict.items()}:
        self.state = self.states_dict[entity_state]
      else:
        self.hass.log('{}Unrecognized state: {}'.format(self.prefix(), entity_state), level='WARNING')

      # Listen for state changes initiated in Home Assistant.
      temp = self.hass.get_state(self.entity)
      assert temp, ('Entity not found: {} {} {}'.format(__name__, self.id, self.entity))
      
      #      self.hass.log('{}Added listen_state <{}> <{}>'.format(self.prefix(), self.entity, self.external_state_callback), level='INFO')
      self.hass.listen_state(self.external_state_callback, self.entity)

    if not self.state:
      self.state = list(self.states)[0]
      self.hass.log('{}Initial state unset - using {}'.format(self.prefix(), self.state.id), level='INFO')

      #    self.hass.log('{}Initializing'.format(self.prefix()), level='INFO')
    for index, state in enumerate(self.states):
      state.initialize(self.hass, self, index)
      #    self.hass.log('{}Initializing DONE'.format(self.prefix()), level='INFO')
      
    #    self.hass.log('{} initial state set to {}'.format(self.prefix(), self.state.id), level='INFO')
    self.change_state(self.state)
    self.state.activate()

    self.hass.run_every(self.feed_callback, datetime.now()+timedelta(seconds=3), 60)


  def feed_callback(self, kwargs):
    self.feed()

      
  def feed(self):
    #    self.hass.log("{} Feed".format(self.prefix()), level='ERROR')
    if self.watchdog_handle != None:
      self.hass.cancel_timer(self.watchdog_handle)
      self.watchdog_handle = None
            
    self.watchdog_handle = self.hass.run_in(self.watchdog, 120)


  def watchdog(self, kwargs):
    self.hass.log("{} Bark!".format(self.prefix()), level='ERROR')

    
  # Function to find an object with certain id
  def find_state(self, state_name):
    if state_name in self.states_dict:
      return self.states_dict[state_name]
    else:
      self.hass.log('{}find_state cannot find {}'.format(self.prefix(), state_name), level='ERROR')
      return None


  def change_state(self, state):
    self.state = state
    if self.entity:
      try:
        self.hass.set_state(self.entity, state=self.state.name)
      except Exception as e:
        self.hass.log('{}set_state cannot find self.state.name = {}'.format(self.prefix(), self.state.name), level='ERROR')
        

  # Call check when something happened
  def check(self):
    #    self.hass.log('{}check'.format(self.prefix()), level='ERROR')
    pass
    
  def external_state_callback(self, entity, attribute, old, new, kwargs):
    if self.state.id != new:
      if debug: self.hass.log('{}Fsm state change (from hass) state={} old={} new={}'.format(self.prefix(), self.state.id, old, new), level='INFO')
      pass
    

  # Helper function to get the dot-format representation of this object
  def get_dot(self):
    dot = ''
    dot += 'label = ' + self.id + ';\n'
    dot += 'labelloc = "t";\n'

    for state in self.states:
      state_label = state.id
      
    for state in self.states:
      dot += state.get_dot() + '\n'
    return 'digraph "' + self.id + '" {{{}}}'.format(dot)


  def log_graph_link(self):
#    link = 'https://stamm-wilbrandt.de/GraphvizFiddle/#{}'.format(
#      quote(self.get_dot()))

    link = 'https://stamm-wilbrandt.de/GraphvizFiddle/2.1.2/#{}'.format(
      quote(self.get_dot()))

#    link = 'https://dreampuf.github.io/GraphvizOnline/#{}'.format(
#        quote(self.get_dot()))
    self.hass.log('{}Transition graph: {}'.format(self.prefix(), link))
    self.hass.log('{}Transition graph2: {}'.format(self.prefix(), self.get_dot()))
    

  
