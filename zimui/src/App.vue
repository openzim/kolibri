<template>
  <Suspense>
    <router-view></router-view>
  </Suspense>
</template>

<style scoped>
:root {
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-text-size-adjust: 100%;

  --bs-body-font-family: var(--bs-font-sans-serif);
  --bs-font-sans-serif: 'Lato';
}

div {
  font-family: 'Lato';
}

@font-face {
  font-family: 'Lato';
  font-weight: 400;
  font-style: normal;
  font-display: swap;
  src: url('./fonts/lato-v24-latin-regular.woff2') format('woff2'),
    /* Chrome 36+, Opera 23+, Firefox 39+, Safari 12+, iOS 10+ */
      url('./fonts/lato-v24-latin-regular.ttf') format('truetype'); /* Chrome 4+, Firefox 3.5+, IE 9+, Safari 3.1+, iOS 4.2+, Android Browser 2.2+ */
}
</style>
