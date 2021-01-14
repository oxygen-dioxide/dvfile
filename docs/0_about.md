# 关于dvfile
dvfile是操作deepvocal dv文件的python库

## dvfile的设计思想
1. 完备。dvfile的目标是支持读取、写入dv文件的一切特性。为此依赖numpy，在效率、轻量、打包exe等方面做出一定牺牲。
2. 互联互通。dvfile对象可以与多种乐谱文件对象互相转换。dvfile目前支持与以下库对象互转。
    - mido
    - music21
    - utaufile（即将被utaupy取代）
3. 用户友好。dvfile主要为python交互式命令行用户优化使用体验。
    - dvfile提供方便的api，如fix修复，transpose移调，quantize量化等。
    - dvfile的对象操作在修改自身的同时会返回自身，可以在一行内完成多个操作：
    ```py
    #将工程向上移调2个半音，量化到32分音符，并显示五线谱
    d.transpose(2).quantize(60).to_music21_score(use_hanzi=True).show()
    ```
