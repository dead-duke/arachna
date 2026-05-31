# TODO

## v1.1.0 — Language & engine presets
- [ ] init.py: вынести пресеты в presets.py
- [ ] presets.py: Godot (project.godot, *.gd, *.tscn, *.tres, *.gdshader)
- [ ] presets.py: Unity (Assets/, *.cs, *.unity, *.prefab)
- [ ] presets.py: C/C++ (src/, include/, *.c, *.cpp, *.h, CMakeLists.txt)
- [ ] presets.py: C# (*.cs, *.csproj, *.sln)
- [ ] presets.py: Swift (*.swift, Package.swift)
- [ ] presets.py: Kotlin/Java (*.kt, *.java, build.gradle, pom.xml)
- [ ] presets.py: Ruby (*.rb, Gemfile, Rakefile)
- [ ] presets.py: PHP (*.php, composer.json)
- [ ] presets.py: Docker (Dockerfile, docker-compose.yml)
- [ ] presets.py: Terraform (*.tf, *.tfvars)
- [ ] formatter.py: добавить расширения в _EXT_LANG (gd, cs, swift, kt, java, rb, php, tf, dockerfile)
- [ ] init.py: автоопределение всех новых типов проектов
- [ ] Бамп __version__ до 1.1.0

## v1.2.0 — Presets as config
- [ ] presets.json: внешний файл с пресетами
- [ ] --preset godot: выбор пресета при инициализации
- [ ] Пользовательские пресеты (кастомный presets.json)

## Backlog
- [ ] Unreal Engine пресет (слишком сложный формат .uasset)
- [ ] Интеграция в IDE (VS Code extension)
- [ ] Web UI для визуального редактора профилей
