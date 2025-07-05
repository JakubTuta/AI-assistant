<script setup>
import { ref, onMounted, computed } from 'vue'

const props = defineProps({
  searchQuery: String
})

const commands = ref({})

const fetchCommands = async () => {
  try {
    const response = await fetch('http://127.0.0.1:5002/commands')
    const data = await response.json()
    // Initialize inputValues for commands with variables
    for (const category in data) {
      for (const commandName in data[category]) {
        if (data[category][commandName].variables) {
          data[category][commandName].inputValues = {}
          data[category][commandName].variables.forEach(variable => {
            data[category][commandName].inputValues[variable.name] = ''
          })
        }
      }
    }
    commands.value = data
  } catch (error) {
    console.error('Error fetching commands:', error)
  }
}

const executeCommand = async (commandName, categoryName, variables = null) => {
  try {
    let url = `http://127.0.0.1:5002/${commandName}`
    if (variables) {
      const params = new URLSearchParams()
      variables.forEach(variable => {
        const value = commands.value[categoryName][commandName].inputValues[variable.name]
        if (value) {
          params.append(variable.name, value)
        }
      })
      url += `?${params.toString()}`
    }
    await fetch(url, { method: 'POST' })
  } catch (error) {
    console.error(`Error executing command ${commandName}:`, error)
  }
}

const filteredCommands = computed(() => {
  if (!props.searchQuery) {
    return commands.value
  }
  const query = props.searchQuery.toLowerCase()
  const filtered = {}
  for (const category in commands.value) {
    for (const commandName in commands.value[category]) {
      const command = commands.value[category][commandName]
      if (command.name.toLowerCase().includes(query)) {
        if (!filtered[category]) {
          filtered[category] = {}
        }
        filtered[category][commandName] = command
      }
    }
  }
  console.log(filtered)
  return filtered
})

onMounted(fetchCommands)
</script>

<template>
  <v-container>
    <v-list lines="two">
      <v-list-group
        v-for="(categoryCommands, categoryName) in filteredCommands"
        :key="categoryName"
      >
        <template v-slot:activator="{ props }">
          <v-list-item
            v-bind="props"
            :title="categoryName.replace('_', ' ')"
          ></v-list-item>
        </template>

        <template v-for="(command, commandName) in categoryCommands" :key="commandName">
          <v-list-item
            v-if="!command.variables"
            @click="executeCommand(commandName, categoryName)"
            :title="command.name"
            link
          ></v-list-item>
          <v-list-group v-else :value="commandName">
            <template v-slot:activator="{ props }">
              <v-list-item
                v-bind="props"
                :title="command.name"
              ></v-list-item>
            </template>
            <v-list-item>
              <v-form @submit.prevent="executeCommand(commandName, categoryName, command.variables)">
                <v-text-field
                  v-for="variable in command.variables"
                  :key="variable.name"
                  :label="variable.description"
                  v-model="command.inputValues[variable.name]"
                  :required="!variable.optional"
                ></v-text-field>
                <v-btn type="submit" color="primary">Execute</v-btn>
              </v-form>
            </v-list-item>
          </v-list-group>
        </template>
      </v-list-group>
    </v-list>
  </v-container>
</template>
