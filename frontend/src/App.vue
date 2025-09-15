<template>
  <v-app>
    <v-main class="d-flex align-center justify-center">
      <v-container>
        <v-row justify="center">
          <v-col cols="12" md="8" lg="6">
            <div v-if="isChecking" class="text-center">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
              <p class="mt-4">Checking server connection...</p>
            </div>
            <div v-else-if="!isConnected" class="text-center">
              <v-alert type="error" class="mb-4">
                <v-alert-title>Server Connection Error</v-alert-title>
                Could not connect to the server on ports 5002 or 5004. Please make sure the server is running.
              </v-alert>
              <v-btn @click="checkConnection" color="primary" variant="outlined">
                Retry Connection
              </v-btn>
            </div>
            <div v-else>
              <h1 class="text-h4 text-center mb-8">AI Assistant</h1>
              <div v-if="serverResponse" class="mb-4 pa-3 bg-blue-lighten-5 rounded-lg">
                <p v-for="(line, index) in serverResponse" :key="index" class="font-weight-medium">{{ line }}</p>
              </div>
              <v-text-field
                label="Search for a command..."
                variant="outlined"
                clearable
                class="mb-8"
                v-model="searchQuery"
              ></v-text-field>
              <CommandButtons :searchQuery="searchQuery" @command-executed="setServerResponse" />
            </div>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import CommandButtons from './components/CommandButtons.vue'
import { isServerAvailable } from './utils/serverUtils.js'

const isConnected = ref(false)
const searchQuery = ref('')
const serverResponse = ref(null)
const isChecking = ref(false)

const checkConnection = async () => {
  isChecking.value = true
  try {
    const available = await isServerAvailable()
    isConnected.value = available
  } catch (error) {
    console.error('Error connecting to the server:', error)
    isConnected.value = false
  } finally {
    isChecking.value = false
  }
}

const setServerResponse = (response) => {
  if (typeof response === 'string') {
    serverResponse.value = [response]
  } else if (Array.isArray(response)) {
    serverResponse.value = response
  } else {
    serverResponse.value = null
  }
}

onMounted(checkConnection)
</script>