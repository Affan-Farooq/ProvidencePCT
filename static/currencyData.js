document.addEventListener('DOMContentLoaded', function(event) {
    var percentChange = document.getElementById('pc24h');
    var pc24h = percentChange.innerText.slice(0, -1);
    var pcFloat = parseFloat(pc24h);

    if (pcFloat > 0) {
        percentChange.style.color = '#82CD47';
    } else {
        percentChange.style.color = '#D80032';
    }
});
