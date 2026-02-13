// Basic JS for small interactive enhancements
document.addEventListener('DOMContentLoaded', function(){
  // Simple confirmation for delete forms
  document.querySelectorAll('form[data-confirm]').forEach(function(f){
    f.addEventListener('submit', function(e){
      var msg = f.getAttribute('data-confirm') || 'Are you sure?';
      if(!confirm(msg)) e.preventDefault();
    });
  });
});
