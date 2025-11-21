use rsscraper::{Html, Selector};   // ❌  use scraper::{Html, Selector};

fn main() {
    let html = Html::parse_document("<p>Hello</p>");
    let sel = Selector::parse("p").unwrap();
    for e in html.select(&sel) {
        println!("{}", e.text().collect::<String>());
    }
}
