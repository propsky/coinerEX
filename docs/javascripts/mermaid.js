document$.subscribe(() => {
  mermaid.initialize({
    startOnLoad: true,
    theme: window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default'
  });
});