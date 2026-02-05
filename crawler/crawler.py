import asyncio
import re
from playwright.async_api import async_playwright

async def get_oil_details():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.liqui-moly.com/en/us/service/oil-guide.html")
        #<button id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll" class="CybotCookiebotDialogBodyButton" tabindex="0" lang="en" fdprocessedid="3t65n8">Allow all cookies</button>
        try:
            cookie_button = "button#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"
            await page.wait_for_selector(cookie_button, timeout=5000)
            await page.click(cookie_button)
        except:
            print("Cookie popup did not appear, skipping.")

    # <a class="nav-link py-4 p-md-4 fs-7 border-0 is-active" data-role="collapsible" tabindex="0" data-toggle="d-none" data-target="#oww-tab-widget-owwtab-vehicleselectblock-0" href="#" data-oww-source="fahrzeugsuche" id="oww-tab-label-widget-owwtab-vehicleselectblock-0" role="tab" data-collapsible="true" aria-controls="oww-tab-widget-owwtab-vehicleselectblock-0" aria-selected="true" aria-expanded="true">
    #                             Vehicle Selection                            </a>
        vehicle_selection = page.locator("a#oww-tab-label-widget-owwtab-vehicleselectblock-0")
        await vehicle_selection.click()
        brand_selector = "select#oww-vs-vehicle-brand"
        await page.wait_for_selector(brand_selector)
        await page.select_option(brand_selector, label="Aston Martin")
        # <select id="oww-vs-vehicle-model" class="form-select form-select-lg" data-bind="options: resultModels().models,
        #                optionsText: function(item) {
        #                    return item.name;
        #                },
        #                value: selectedModelId,
        #                optionsValue: 'id',
        #                optionsCaption: 'Model',
        #                attr: { disabled: resultModels().models.length === 0 },
        #                afterRender: afterRenderModels" fdprocessedid="gwvfr8"><option value="" hidden="hidden">Model</option><option value="3e01ed537e653090">Cygnet (2011-2013)</option><option value="5cd130c25d803ca1">DB11 (2016-2023)</option><option value="dee3c090cbde474a">DB7 (1994-2004)</option><option value="eec5d4e2b79722a7">DB9 (2003-2016)</option><option value="e56d3d5d99911ca1">DBS (2008-2012)</option><option value="fd4e681ae423e85f">DBS Superlegerra (2018- )</option><option value="50273f42e4c70d0e">DBX (2020- )</option><option value="9c6501a4171a9bea">One-77 (2011-2012)</option><option value="f81ad3b3b47b4b4d">Rapide (2010-2019)</option><option value="72d7ee3c2e65ac4a">V12 Vanquish (2001-2007)</option><option value="044663765933dce4">V12 Vantage (2010-2018)</option><option value="c4d032a9aad74666">V8 (1982-2001)</option><option value="c1efa5e34869b86c">V8 Vantage (2005-2018)</option><option value="6347be04e57c4486">Vanquish (2012-2018)</option><option value="3f8efe4167f36c16">Vantage (2018- )</option><option value="1ca5cf14a59a22bd">Virage (2011-2012)</option>
        #         </select>
        await page.wait_for_timeout(1000)
        model_selector = "select#oww-vs-vehicle-model"
        await page.wait_for_selector(model_selector)
        await page.select_option(model_selector, label="Cygnet (2011-2013)")
        # await page.select_option("select >> nth=1", index=1) 
        await page.wait_for_timeout(1000)

        type_selector = "select#oww-vs-vehicle-vehicle-type"
        # <select id="oww-vs-vehicle-vehicle-type" class="form-select form-select-lg" data-bind="options: resultTypes().types,
        #                optionsText: function(item) {
        #                    return item.name;
        #                },
        #                value: selectedTypeId,
        #                optionsCaption: 'Vehicle type',
        #                attr: { disabled: resultTypes().types.length === 0 },
        #                afterRender: afterRenderTypes" fdprocessedid="23rubp"><option value="" hidden="hidden">Vehicle type</option><option value="">Cygnet 1.3 VVT-i (2011-2013)</option>
        #         </select>
        await page.wait_for_selector(type_selector)
        await page.select_option(type_selector, index=1)
        # <strong class="product-item-name mb-1">Top Tec 4210 SAE 0W-30</strong>
        # <a href="https://www.liqui-moly.com/en/us/tinyurl/P005106" title="Top Tec 4210 SAE 0W-30" target="_self" class="text-body product-item-info position-relative d-flex h-100">
        
        #     <div class="product-item-photo mb-3 text-center">
        #         <img src="https://liquimoly.cloudimg.io/width/110/n/https://www.liqui-moly.com/media/catalog/product/2/2/22158_Top_Tec_4210_0W_30_5l_bd45.png?lmCacheDate=20260203" alt="Top Tec 4210 SAE 0W-30">
        #     </div>

        #     <div class="d-flex flex-column product-item-details-wrapper w-100">
        #         <div class="d-flex justify-content-between product-item-details">
        #             <div class="d-flex flex-column product-item-title fs-10 fs-md-9 w-100">
        #                 <div class="product-item-title-and-rating">
        #                     <strong class="product-item-name mb-1">Top Tec 4210 SAE 0W-30</strong>
        #                 </div>
        #             </div>
        #         </div>

        #         <div class="text-decoration-none text-reset">
        #             <div class="mt-2">
        #                 <strong class="d-inline-block fs-11 fs-md-10 text-primary more-link-wrap">                            show <span class="text-nowrap more-link" data-limo-link="">details</span></strong>
        #             </div>
        #         </div>
        #     </div>

        #         </a>
        # <strong class="product-item-name mb-1">Top Tec 4210 SAE 0W-30</strong>
        await page.wait_for_selector("strong.product-item-name")
        products = await page.locator("strong.product-item-name").all_text_contents()
        print("\n--- Results Found ---")
        for product in products:
            viscosity = re.search(r'\d+W-\d+', product)
            if viscosity:
                print(f"Viscosity: {viscosity.group()}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_oil_details())