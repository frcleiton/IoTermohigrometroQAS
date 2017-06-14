var lmin = parseInt(document.getElementById('par_min').value);
var lmax = parseInt(document.getElementById('par_max').value);
var ltemp = parseInt(document.getElementById('par_temp').value);
if (ltemp < lmin) {
      document.getElementById("temperatura").style.color = "white";
      document.getElementById("temperatura").style.backgroundColor = "blue";
} else if (ltemp > lmax) {
      document.getElementById("temperatura").style.color = "white";
      document.getElementById("temperatura").style.backgroundColor = "red";
}