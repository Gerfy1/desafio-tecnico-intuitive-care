<template>
  <nav>
    <a href="#" @click="currentView = 'tabela'">Operadoras</a> |
    <a href="#" @click="currentView = 'dashboard'">Dashboard (Gráfico)</a>
  </nav>
  
  <component :is="currentView === 'tabela' ? TabelaOperadoras : Dashboard" />
</template>

<script setup>
import { ref } from 'vue';
import TabelaOperadoras from './components/TabelaOperadoras.vue';
import Dashboard from './components/Dashboard.vue';

const currentView = ref('tabela');
</script>

<style>
nav { padding: 20px; background: #eee; margin-bottom: 20px; }
a { margin-right: 10px; cursor: pointer; color: blue; text-decoration: underline; }
</style>