# xpath 定义
class X:
    VIDEOS = '//*[@data-e2e="user-post-item-list"]/div'
    VIDEO  = '//*[@data-e2e="user-post-item-list"]/div[1]'
    CLOSE_BUTTON = '//*[@data-e2e="browse-close"]'
    DATE = '//*[@data-e2e="browser-nickname"]/span[3]'
    LIKES = '//*[@data-e2e="browse-like-count"]'
    # ACCOUNT_ERROR   = '//*[@class="css-1y4x9xk-PTitle emuynwa1"]'
    ACCOUNT_ERROR   = '//*[contains(@class, "emuynwa1")]'
    LIVE = '//*[@class="css-x6y88p-DivItemContainerV2 e19c29qe17"]'
    PIN = '//*[@data-e2e="video-card-badge"]'

    VERIFY_CODE = '//*[starts-with(@id, ":")]/div/div[1]/div/button'
    REFRESH_BUTTON = '//*[@id="main-content-others_homepage"]/div/div[2]/main/div/button|//*[@id="main-content-others_homepage"]/div/main/div/button'
    LOGIN = '//*[@id="loginContainer"]/div/div/div[3]/div/div[2]'