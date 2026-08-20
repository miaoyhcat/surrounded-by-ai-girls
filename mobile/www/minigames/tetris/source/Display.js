/**
 * Tetris Display
 */
export default class Display {

    /**
     * Tetris Display constructor
     */
    constructor() {
        this.current   = "mainScreen";
        this.container = document.querySelector("#container");
        this.header    = document.querySelector(".messages h2");
        this.paragraph = document.querySelector(".messages p");

        this.messages  = {
            mainScreen : [ "俄罗斯方块",     "选择起始关卡" ],
            paused     : [ "暂停",      "Continue with the game?"   ],
            continuing : [ "继续",   "Continue with the game?"   ],
            gameOver   : [ "游戏结束",   "写下你的名字"           ],
            highScores : [ "排行榜", "选择关卡"            ],
            help       : [ "帮助",       "操作说明"            ]
        };
    }


    /**
     * Gets the Game Display
     * @returns {String}
     */
    get() {
        return this.current;
    }

    /**
     * Sets the Game Display
     * @param {String} current
     * @returns {Display}
     */
    set(current) {
        this.current = current;
        return this;
    }


    /**
     * Show the message
     */
    show() {
        this.container.className = this.current;
        this.header.innerHTML    = this.messages[this.current][0];
        this.paragraph.innerHTML = this.messages[this.current][1];
    }

    /**
     * Hide the message
     */
    hide() {
        this.container.className = "playing";
    }



    /**
     * Returns true if the current is in the main screen
     * @returns {Boolean}
     */
    get isMainScreen() {
        return this.current === "mainScreen";
    }

    /**
     * Returns true if the current is in playing mode
     * @returns {Boolean}
     */
    get isPlaying() {
        return this.current === "playing";
    }

    /**
     * Returns true if the current is in paused mode
     * @returns {Boolean}
     */
    get isPaused() {
        return this.current === "paused";
    }
}
