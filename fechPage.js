const puppeteer = require('puppeteer');
const fs = require('fs').promises;

const url = 'https://cloudjune.com'; // Replace with the desired URL
const outputFilePath = './output.txt'; // Specify the output file path

let previousContent = '';

async function fetchPageContent() {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    
    await page.goto(url, { waitUntil: 'networkidle0' });

    // Extract text content using browser's JavaScript context
    const textContent = await page.evaluate(() => {
        return document.body.innerText;
    });

    await browser.close();
    return textContent;
}

async function checkForChanges() {
    const currentContent = await fetchPageContent();

    if (currentContent !== previousContent) {
        // Save the text content to the specified file
        await fs.writeFile(outputFilePath, currentContent);
        console.log('Content changed and saved to', outputFilePath);
        previousContent = currentContent; // Update the previous content
    }

    // Poll every 24 hours
    setTimeout(checkForChanges, 86400000); // 24 hours in milliseconds
}

// Start the polling process
checkForChanges().catch(error => {
    console.error('Error in polling:', error);
});
