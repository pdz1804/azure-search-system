// Utility to get a random default image from public folder
// Images expected: /sea_default_01.jpg ... /sea_default_05.jpg

const defaultImages = [
  '/sea_default_01.jpg',
  '/sea_default_02.jpg',
  '/sea_default_03.jpg',
  '/sea_default_04.jpg',
  '/sea_default_05.jpg'
];

export function getRandomDefaultImage() {
  const index = Math.floor(Math.random() * defaultImages.length);
  return defaultImages[index];
}

export function withRandomFallback(src) {
  return src || getRandomDefaultImage();
}


