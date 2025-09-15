<script setup>
import { ref, onMounted, computed } from 'vue'
import { makeServerRequest } from '../utils/serverUtils.js'

const props = defineProps({
  searchQuery: String
})

const emit = defineEmits(['command-executed'])

const commands = ref({})
const isLoading = ref(false)
const error = ref(null)

const fetchCommands = async () => {
  isLoading.value = true
  error.value = null
  try {
    const result = await makeServerRequest('/commands')
    const data = result.data
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
  } catch (err) {
    console.error('Error fetching commands:', err)
    error.value = err.message
    emit('command-executed', `Error: ${err.message}`)
  } finally {
    isLoading.value = false
  }
}

const executeCommand = async (commandName, categoryName, variables = null) => {
  isLoading.value = true
  error.value = null
  try {
    let endpoint = `/${commandName}`
    const options = { method: 'POST' }
    
    if (variables) {
      const params = new URLSearchParams()
      variables.forEach(variable => {
        const value = commands.value[categoryName][commandName].inputValues[variable.name]
        if (value) {
          params.append(variable.name, value)
        }
      })
      endpoint += `?${params.toString()}`
    }
    
    const result = await makeServerRequest(endpoint, options)
    emit('command-executed', result.data.response)
  } catch (err) {
    console.error(`Error executing command ${commandName}:`, err)
    error.value = err.message
    emit('command-executed', `Error executing ${commandName}: ${err.message}`)
  } finally {
    isLoading.value = false
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
    <div v-if="isLoading" class="text-center">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
      <p class="mt-2">Processing request...</p>
    </div>
    
    <v-alert v-if="error" type="error" class="mb-4" dismissible @click:close="error = null">
      {{ error }}
    </v-alert>
    
    <v-list v-if="!isLoading" lines="two">
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
            :disabled="isLoading"
            link
          ></v-list-item>
          <v-list-group v-else :value="commandName">
            <template v-slot:activator="{ props }">
              <v-list-item
                v-bind="props"
                :title="command.name"
                :disabled="isLoading"
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
                  :disabled="isLoading"
                ></v-text-field>
                <v-btn type="submit" color="primary" :loading="isLoading">Execute</v-btn>
              </v-form>
            </v-list-item>
          </v-list-group>
        </template>
      </v-list-group>
    </v-list>
  </v-container>
</template>
