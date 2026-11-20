/* 3D-модель квартиры: поворот вокруг вертикальной оси, зум щипком или колесом. Модель — .glb рядом со страницами. */
(function () {
  'use strict';
  var wrap = document.querySelector('.viewer3d');
  if (!wrap) return;
  var status = wrap.querySelector('.v3-status');
  function say(t) { status.textContent = t; status.hidden = !t; }
  if (!window.THREE || !THREE.GLTFLoader || !THREE.OrbitControls) {
    say('3D-модель не загрузилась. Рендеры есть на странице варианта.');
    return;
  }
  var renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.68;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  wrap.appendChild(renderer.domElement);

  var scene = new THREE.Scene();
  scene.background = new THREE.Color(0xE9ECEB);
  if (THREE.RoomEnvironment) {
    var pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new THREE.RoomEnvironment(), 0.04).texture;
  }
  var camera = new THREE.PerspectiveCamera(32, 1, 0.1, 200);
  var controls = new THREE.OrbitControls(camera, renderer.domElement);
  var polar = 50 * Math.PI / 180;
  controls.enablePan = false;
  controls.enableDamping = true;
  controls.minPolarAngle = polar;
  controls.maxPolarAngle = polar;
  controls.minDistance = 5;
  controls.maxDistance = 34;

  scene.add(new THREE.HemisphereLight(0xffffff, 0xbdb6a8, 0.2));
  var sun = new THREE.DirectionalLight(0xfff4e6, 0.9);
  sun.position.set(-7, 15, 9);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  var sc = sun.shadow.camera; sc.left = -11; sc.right = 11; sc.top = 11; sc.bottom = -11; sc.far = 60;
  scene.add(sun);
  var ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.ShadowMaterial({ opacity: 0.16 }));
  ground.rotation.x = -Math.PI / 2; ground.position.y = -0.02; ground.receiveShadow = true;
  scene.add(ground);

  function resize() {
    var w = wrap.clientWidth, h = wrap.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / Math.max(1, h);
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  resize();

  new THREE.GLTFLoader().load(wrap.getAttribute('data-model'), function (g) {
    g.scene.traverse(function (o) { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(g.scene);
    var box = new THREE.Box3().setFromObject(g.scene);
    var c = box.getCenter(new THREE.Vector3());
    var r = box.getSize(new THREE.Vector3()).length() * (wrap.clientWidth < 600 ? 1.25 : 0.95);
    controls.target.copy(c);
    camera.position.set(c.x - r * Math.sin(polar) * 0.5, c.y + r * Math.cos(polar), c.z + r * Math.sin(polar) * 0.87);
    controls.update();
    say('');
  }, undefined, function () { say('Не удалось загрузить модель.'); });

  (function loop() { requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); })();
})();
