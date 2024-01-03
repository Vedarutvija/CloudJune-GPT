const puppeteer = require('puppeteer');
const fs = require('fs').promises;

const mainUrl = 'https://cloudjune.com';
const outputFilePath = './out.txt';

let allContent = '';
let visitedLinks = new Set(); // Set to store visited links

async function fetchPageContent(url) {
    try {
        const browser = await puppeteer.launch();
        const page = await browser.newPage();
        
        await page.goto(url, { waitUntil: 'networkidle0' });

        // Exclude header, footer, or other elements by their selectors
        await page.evaluate(() => {
            const header = document.querySelector('header');
            const footer = document.querySelector('footer');
            
            if (header) header.remove();
            if (footer) footer.remove();
            
            // Add additional selectors as needed
        });

        const textContent = await page.evaluate(() => {
            return document.body.innerText;
        });

        await browser.close();
        return textContent;
    } catch (error) {
        console.error(`Error fetching content from ${url}:`, error.message);
        return ''; // Return empty string for invalid URLs
    }
}

async function fetchAllLinks() {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    await page.goto(mainUrl, { waitUntil: 'networkidle0' });

    const links = await page.evaluate(() => {
        const anchorTags = document.querySelectorAll('a');
        return Array.from(anchorTags).map(a => a.href);
    });

    await browser.close();
    return links;
}

async function fetchAndConcatenateContent() {
    const links = await fetchAllLinks();
    for (const link of links) {
        if (!visitedLinks.has(link)) { // Check if link has not been visited
            visitedLinks.add(link);    // Mark link as visited
            console.log(`Fetching content from: ${link}`); // Print the current link
            const content = await fetchPageContent(link);
            if (content) {
                allContent += content + '\n\n';  // Separate content from different pages with two newlines
                allContent += '-----------------------------------------------------------------\n\n'; 
            }
        }
    }

    await fs.writeFile(outputFilePath, allContent);
    console.log('Content concatenated and saved to', outputFilePath);
}


// Start the process
fetchAndConcatenateContent().catch(error => {
    console.error('Error:', error);
});
