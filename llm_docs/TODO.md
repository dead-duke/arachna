# TODO

## v1.1.0 — Language & engine presets
- [x] init.py: вынести пресеты в presets.py
- [x] presets.py: Godot (project.godot, *.gd, *.tscn, *.tres, *.gdshader)
- [x] presets.py: Unity (Assets/, *.cs, *.unity, *.prefab)
- [x] presets.py: C/C++ (src/, include/, *.c, *.cpp, *.h, CMakeLists.txt)
- [x] presets.py: C# (*.cs, *.csproj, *.sln)
- [x] presets.py: Swift (*.swift, Package.swift)
- [x] presets.py: Kotlin/Java (*.kt, *.java, build.gradle, pom.xml)
- [x] presets.py: Ruby (*.rb, Gemfile, Rakefile)
- [x] presets.py: PHP (*.php, composer.json)
- [x] presets.py: Docker (Dockerfile, docker-compose.yml)
- [x] presets.py: Terraform (*.tf, *.tfvars)
- [x] formatter.py: добавить расширения в _EXT_LANG (gd, cs, swift, kt, java, rb, php, tf, dockerfile)
- [x] init.py: автоопределение всех новых типов проектов
- [x] Бамп __version__ до 1.1.0

## v1.2.0 — Presets as config
- [ ] presets.json: внешний файл с пресетами
- [ ] --preset godot: выбор пресета при инициализации
- [ ] Пользовательские пресеты (кастомный presets.json)

## Backlog
- [ ] Unreal Engine пресет (слишком сложный формат .uasset)
- [ ] Интеграция в IDE (VS Code extension)
- [ ] Web UI для визуального редактора профилей
