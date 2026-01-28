<template>
  <div class="app-layout">
    <nav class="navbar">
      <div class="nav-brand">Intuitive Care Teste</div>
      <div class="nav-links">
        <router-link to="/" class="nav-item">Operadoras</router-link>
        <router-link to="/dashboard" class="nav-item">Dashboard</router-link>
      </div>
    </nav>
    
    <main class="content">
      <router-view></router-view>
    </main>
  </div>
</template>

<style>
body { margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; }
.navbar { background-color: #2c3e50; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.nav-brand { font-size: 1.2rem; font-weight: bold; }
.nav-links { display: flex; gap: 20px; }
.nav-item { color: #ecf0f1; text-decoration: none; padding: 5px 10px; border-radius: 4px; transition: background 0.3s; }
.nav-item:hover, .router-link-active { background-color: #34495e; color: #42b983; }
.content { padding: 2rem; max-width: 1200px; margin: 0 auto; background: white; min-height: 80vh; box-shadow: 0 0 10px rgba(0,0,0,0.05); margin-top: 20px; border-radius: 8px; }
</style>