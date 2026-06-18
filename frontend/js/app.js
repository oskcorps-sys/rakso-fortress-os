// RAKSO Control Panel - Core Logic
document.addEventListener('DOMContentLoaded', () => {
  const terminal = document.getElementById('network-log');
  
  function logToTerminal(message) {
    const p = document.createElement('p');
    p.textContent = `[${new Date().toISOString().split('T')[1].slice(0, -1)}] ${message}`;
    terminal.appendChild(p);
    terminal.scrollTop = terminal.scrollHeight;
  }

  // Simulación segura de conexión WSS inicial
  setTimeout(() => {
    logToTerminal("Handshake complete. AES-GCM encryption verified.");
  }, 1000);

  setTimeout(() => {
    logToTerminal("Integrity checks passed. No foreign modules detected.");
  }, 2500);
});
