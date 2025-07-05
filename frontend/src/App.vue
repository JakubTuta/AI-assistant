<template>
  <v-app>
    <v-main class="d-flex align-center justify-center">
      <v-container>
        <v-row justify="center">
          <v-col cols="12" md="8" lg="6">
            <div v-if="!isConnected" class="text-center text-red-500 text-h5">
              Error: Could not connect to the server.
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

const isConnected = ref(false)
const searchQuery = ref('')
const serverResponse = ref(null)

const checkConnection = async () => {
  try {
    const response = await fetch('http://127.0.0.1:5002/ping')
    if (response.ok) {
      isConnected.value = true
    }
  } catch (error) {
    console.error('Error connecting to the server:', error)
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