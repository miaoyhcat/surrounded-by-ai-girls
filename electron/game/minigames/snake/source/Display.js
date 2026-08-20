/**
 * Snake Display
 */
export default class Display {

    /**
     * Snake Display constructor
     */
    constructor() {
        this.current   = "mainScreen";
        this.container = document.querySelector("#container");
        this.header    = document.querySelector(".messages h2");
        this.paragraph = document.querySelector(".messages p");

        this.messages  = {
            mainScreen : [ "贪吃蛇",      "选择关卡"     ],
            paused     : [ "暂停",      "继续游戏？" ],
            continuing : [ "继续",   "继续游戏？" ],
            gameOver   : [ "游戏结束",   "写下你的名字"    ],
            highScores : [ "排行榜", "选择关卡"     ],
            help       : [ "帮助",       "操作说明"     ]
        };
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
     * Sets the container class
     * @returns {Void}
     */
    setClass() {
        this.container.className = this.current;
    }

    /**
     * Show the message
     * @returns {Void}
     */
    show() {
        this.header.innerHTML    = this.messages[this.current][0];
        this.paragraph.innerHTML = this.messages[this.current][1];
        this.setClass();
    }

    /**
     * Hide the message
     * @returns {Void}
     */
    hide() {
        this.container.className = "playing";
    }



    /**
     * Returns true if is starting the game
     * @returns {Boolean}
     */
    get isStarting() {
        return this.current === "starting";
    }

    /**
     * Returns true if is playing the game
     * @returns {Boolean}
     */
    get isPlaying() {
        return this.current === "playing";
    }

    /**
     * Returns true if is demoing the game
     * @returns {Boolean}
     */
    get isDemoing() {
        return this.current === "demo";
    }
}
