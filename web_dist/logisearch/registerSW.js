if('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js', { scope: './' })
      .then(reg => console.log('LogiSearch SW Registered', reg))
      .catch(err => console.error('LogiSearch SW Failed', err));
  });
}