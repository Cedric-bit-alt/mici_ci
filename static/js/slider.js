document.addEventListener("DOMContentLoaded", function () {
    const hero = document.querySelector(".hero-section");

    const images = [
        "/static/images/images (1).jpeg",
        "/static/images/images (3).jpeg",
        "/static/images/images (6).jpeg",
        "/static/images/téléchargement (1).jpeg"
        
    ];

    let index = 0;

    setInterval(() => {
        index = (index + 1) % images.length;
        hero.style.backgroundImage = `url("${images[index]}")`;
    }, 3000);
});
