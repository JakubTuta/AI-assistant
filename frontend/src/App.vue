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
              <v-text-field
                label="Search for a command..."
                variant="outlined"
                clearable
                class="mb-8"
                v-model="searchQuery"
              ></v-text-field>
              <CommandButtons :searchQuery="searchQuery" />
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

onMounted(checkConnection)
</script>