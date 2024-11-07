import mysql.connector
import sys
from datetime import date

def callproducts():
    #set up database
    cnx = mysql.connector.connect(user='com303gcortgras', password='gc45367gc',
                              host='136.244.224.221',
                              database='com303fpegj')
    cursor = cnx.cursor()
    
    products = "select 'product_name', 'price' union all select product_name, price from product"
    cursor.execute(products)
    presults = cursor.fetchall()
    for row in presults:
        row_str = str(row).replace('\'', '').replace('(', '').replace(')', '')
        print(row_str + "$")


def orders(membership):
    #set up database
    cnx = mysql.connector.connect(user='com303gcortgras', password='gc45367gc',
                              host='136.244.224.221',
                              database='com303fpegj')
    cursor = cnx.cursor()

    print("\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    print("Where is your closest Costco?\n")

    #cprints out store locations
    storelocations = "select s_city from store"
    cursor.execute(storelocations)
    slresults = cursor.fetchall()
    numletter=ord("A")
    for row in slresults:
        row_str = str(row).replace('\'', '').replace('(', '').replace(')', '')
        print(chr(numletter) + ":" + " " + row_str)
        numletter = numletter+1

        
    storechoice = input("\nPlease type the letter that corresponds with your city:\n")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    #designated store choices and associated warehouse
    if storechoice in ["a", "A"]:
        store_id = "S003"
        w_id = "W006"
    elif storechoice in ["b", "B"]:
        store_id = "S005"
        w_id = "W002"
    elif storechoice in ["c", "C"]:
        store_id = "S006"
        w_id = "W008"
    elif storechoice in ["d", "D"]:
        store_id = "S007"
        w_id = "W010"
    elif storechoice in ["e", "E"]:
        store_id = "S012"
        w_id = "W003"
    elif storechoice in ["f", "F"]:
        store_id = "S032"
        w_id = "W001"
    elif storechoice in ["g", "G"]:
        store_id = "S038"
        w_id = "W005"
    elif storechoice in ["h", "H"]:
        store_id = "S043"
        w_id = "W004"
    elif storechoice in ["i", "I"]:
        store_id = "S044"
        w_id = "W007"
    elif storechoice in ["j", "J"]:
        store_id = "S045"
        w_id = "W009"

    #lists all products
    callproducts()

    #cart dictionary
    cart = {}
    
    
    while True: #while statement to allow user to add multiple items to cart
        productchoice = input("\nPlease type the exact name of the product you'd like to add to your cart, or type 'done' to stop adding items:\n")
        if productchoice == "done":
            break
        
        #psimultaneously checks if product exists, and gets the product id
        checkproduct = "select product_id from product where product_name = %s"
        parameter = (productchoice,)
        cursor.execute(checkproduct, parameter)
        cpresults = cursor.fetchone()
        if not cpresults:
            print("\n~~~That item isn't at our Costco! Please choose from the list above:~~~\n")
            continue

        #check if item is in stock/ if there is enough for the user to purchase
        query = "select current_amt from storeinventory where store_id = %s and product_id = %s"
        cursor.execute(query, (store_id, cpresults[0]))
        insi = cursor.fetchone()[0]
        if int(insi) == 0:
            print("\nThat product is currently out of stock. Please choose another item!")
            continue
        quantity = int(input("Please enter the quantity of this item you'd like to add: "))
        if quantity == 0:
            print("You can't add 0!")
            continue
        if int(insi) < int(quantity):
           print("There is currently less of that item in stock than you'd like! Please choose a smaller amount, or choose another item.")
           continue

        #adds product and quantity to dictionary
        cart[productchoice] = quantity
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("\n~~~ Your cart contains the following items:", cart, "~~~")

    if len(cart) == 0:
        print("Hmmmm, your cart is empty, that doesn't seem right. Please try again!")
        sys.exit()

    #creates new transaction id for invoices
    else:
        maxtransactionid = "select max(transaction_id) from invoices"
        cursor.execute(maxtransactionid)
        mtresults = cursor.fetchone()
        last_number = int(mtresults[0][1:])  # extract the number from the ID and convert it to an integer
        new_number = last_number + 1  # increment the number by 1
        new_transaction_id = 'T{:05d}'.format(new_number)


        #calculate price of cart
        productlist = list(cart.keys())
        pricelist = []
        x=0
        total_cost = 0
        for i in cart:
            query = "SELECT price FROM product WHERE product_name = %s"
            
            cursor.execute(query, (productlist[x],))
            price = cursor.fetchone()[0]
            pricelist.append(price)
            total_cost += price * cart[productlist[x]]
            x = x+1
    
        print("Total Price:", "$",total_cost)

        #asks user to confirm purchase (literally the only option)
        confirm = input("Confirm? (please type confirm)\n")
        if confirm in ["confirm", "Confirm"]:

            #calculate product ids and quantity of each product in list
            a = 0
            idlist = []
            quantitylist = []
            for product_name, quantity in cart.items(): # loop through cart dictionary
                query = "SELECT product_id FROM product WHERE product_name = %s"
                cursor.execute(query, (product_name,))
                product_id = cursor.fetchone()[0]
                idlist.append(product_id)
                quantitylist.append(quantity)

            #update each product quantity in the storeinventory
                query = ("UPDATE storeinventory SET current_amt = current_amt - %s WHERE product_id = %s AND store_id = %s")
                cursor.execute(query, (quantitylist[a], idlist[a], store_id))
                cnx.commit()

            #figure out if current_amt of selected product is smaller than min_amt
                query = ("SELECT current_amt, min_amt FROM storeinventory WHERE product_id = %s AND store_id = %s")
                cursor.execute(query, (idlist[a], store_id))
                result = cursor.fetchone()

            #if it is select the amount from the warehouse associated with the store
                if int(result[0]) < int(result[1]):
                    query = "select current_amt from warehouseinventory where product_id = %s and w_id = %s"
                    cursor.execute(query, (idlist[a], w_id))
                    resultwi = cursor.fetchone()[0] #current stock in the warehouse inventory
                    amttostock = int(50 - int(result[0])) #amount needed to get storeinventory back to 50
                    resultwi = int(resultwi)

                    #if there's nothing else to restock, the code stops, vendor has to restock
                    if resultwi == 0:
                        break

                    #if the current stock in the warehouse is less than the amount needed to get storeinventory stock to 50, it adds everything from warehouseinventory
                    elif resultwi < amttostock:
                        query = "update warehouseinventory set current_amt = current_amt - current_amt where product_id = %s and w_id = %s"
                        cursor.execute(query, (idlist[a], w_id))
                        cnx.commit()
                        query = "update storeinventory set current_amt = current_amt + %s where product_id = %s and store_id = %s"
                        cursor.execute(query, (resultwi, idlist[a], store_id))
                        cnx.commit()

                    #if the current stock in the warehouse is larger than the amount needed to get storeinventory stock to 50, it adds the correct amount
                    elif resultwi > amttostock:
                        query = "update warehouseinventory set current_amt = current_amt - %s where product_id = %s and w_id = %s"
                        cursor.execute(query, (amttostock, idlist[a], w_id))
                        cnx.commit()
                        query = "update storeinventory set current_amt = current_amt + %s where product_id = %s and store_id = %s"
                        cursor.execute(query, (amttostock, idlist[a], store_id))
                        cnx.commit()
                a+=1
                        
            


            #get the date
            today = date.today()

            #update invoices
            y = 0
            for i in idlist:
                query = ("INSERT INTO invoices (transaction_id, total, membership_id, store_id, product_id, date, pay_method)"
                         "VALUES (%s, %s, %s, %s, %s, %s, %s)")
                cursor.execute(query, (new_transaction_id, total_cost, membership, store_id, idlist[y], today, "card"))
                cnx.commit()
                y = y + 1

            print("\n~~~Order submitted to invoices and store inventory updated. You can now pick up your order from your chosen store!~~~")

        #if the user doesn't confirm
        elif confirm not in ["confirm", "Confirm"]:
            print("ok whatever i guess bye")
            sys.exit()
        
def accessdatabase():
    #set up database
    cnx = mysql.connector.connect(user='com303gcortgras', password='gc45367gc',
                                  
                              host='136.244.224.221',
                              database='com303fpegj')
    cursor = cnx.cursor()
    
    #choose which table you'd like to view the contents of
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    print("Which table would you like to access?:")
    while True:
        choosetable = input("\nA: Invoices\nB: Membership\nC: Product\nD: Store\nE: Store Inventory\nF: Vendor\nG: Warehouse\nH: Warehouse Inventory\nI: Quit\n")
        if choosetable in ["a", "A"]:
              iquery = "select * from invoices"
              cursor.execute(iquery)
              iresult = cursor.fetchall()
              for row in iresult:
                  print(row)
        elif choosetable in ["b", "B"]:
            mquery = "select * from membership"
            cursor.execute(mquery)
            mresult = cursor.fetchall()
            for row in mresult:
                print(row)
        elif choosetable in ["c", "C"]:
            pquery = "select * from product"
            cursor.execute(pquery)
            presult = cursor.fetchall()
            for row in presult:
                print(row)
        elif choosetable in ["d", "D"]:
            squery = "select * from store"
            cursor.execute(squery)
            sresult = cursor.fetchall()
            for row in sresult:
                print(row)
        elif choosetable in ["e", "E"]:
            siquery = "select * from storeinventory"
            cursor.execute(siquery)
            siresult = cursor.fetchall()
            for row in siresult:
                print(row)
        elif choosetable in ["f", "F"]:
            vquery = "select * from vendor"
            cursor.execute(vquery)
            vresult = cursor.fetchall()
            for row in vresult:
                print(row)
        elif choosetable in ["g", "G"]:
            wquery = "select * from warehouse"
            cursor.execute(wquery)
            wresult = cursor.fetchall()
            for row in wresult:
                print(row)
        elif choosetable in ["h", "H"]:
            wiquery = "select * from warehouseinventory"
            cursor.execute(wiquery)
            wiresult = cursor.fetchall()
            for row in wiresult:
                print(row)
        elif choosetable in ["i", "I"]:
            sys.exit()
        else:
            print("Please choose a valid option")

            
def restock():
    #set up database
    cnx = mysql.connector.connect(user='com303gcortgras', password='gc45367gc',
                              host='136.244.224.221',
                              database='com303fpegj')
    cursor = cnx.cursor()

    #vendor ID choice
    vendorid = input("\n~~~Please enter your vendor ID~~~\n(For Peitzsch ease: V001 = Coca Cola, V002 = Pepsi, V003 = Clothing Warehouse, V004 = Associated Grocers, V005 = HomeGoods Vendor, V006 = Dairy Farm)\n")
    while vendorid not in ["V001", "V002", "V003", "V004", "V005", "V006"]:
        print("Please enter a valid ID")
        vendorid = input("")

    #while statement allows for user to change the warehouse theyre looking to restock    
    while True:
        print("\nWhich Warehouse are you looking to restock?")
        warehouselocation = input("W001: New York\nW002: Los Angeles\nW003: Chicago\nW004: Houston\nW005: Philadelphia\nW006: Phoenix\nW007: San Antonio\nW008: San Diego\nW009: Dallas\nW010: San Franciso\nQuit\n(Please type the ID associated with the location or type ""Quit"")\n")
        if warehouselocation in ["quit" or "Quit"]:
            sys.exit()
        while warehouselocation not in ["W001", "W002", "W003", "W004", "W005", "W006", "W007", "W008", "W009", "W010"]:
            print("Please choose a valid warehouse")
            warehouselocation = input("")

        #if they choose a valid warehouse
        else:
            while True:
                #selects all products that match vendor id and warehouse
                query = "select * from warehouseinventory where vendor_id = %s and w_id = %s"
                cursor.execute(query, (vendorid, warehouselocation))
                result = cursor.fetchall()
                restockchoice = input("\nWould you like to restock or would you like to choose another location?\nA: Restock\nB: Choose another location\n")

                #if they choose to restock
                if restockchoice in ["a", "A"]:
                    products=[] #list that holds the product name
                    stock = [] #list that holds the current stock

                    #query that is able to display product name and stock rather than product id and stock
                    query = "SELECT p.product_name, wi.current_amt FROM warehouseinventory wi JOIN product p ON wi.product_id = p.product_id WHERE wi.vendor_id = %s AND wi.w_id = %s"
                    cursor.execute(query, (vendorid, warehouselocation))
                    result=cursor.fetchall()

                    #adds product name to list and product stock to list
                    for row in result:
                        products.append(row[0])
                        stock.append(row[1])

                    x=0 #increments per item in list
                    y=1 #numbers the list of the products
                    print("\n")

                    #prints out all products within certain vendor and chosen warehouse
                    for i in products:
                        print(y, products[x], "- Current Stock:", stock[x] )
                        x+=1
                        y+=1

                    
                    while True:
                        productchoice = input("\nPlease type the exact name of the product you'd like to restock, or type 'Quit' to exit:\n")
                        if productchoice.lower() == "quit":
                            sys.exit()

                        #checks if it is a valid product while simultaneously getting the product id
                        checkproduct = "select product_id from product where product_name = %s"
                        parameter = (productchoice,)
                        cursor.execute(checkproduct, parameter)
                        cpresults = cursor.fetchone()
                        if cpresults is None:
                            print("\n~~~That item isn't at our Costco! Please choose from the list above:~~~\n")

                        #if its a valid product, it then asks the vendor how much of that product they'd like to restock
                        else:    
                            n=0
                            amount = input("How many items would you like to add?\n")

                            #query to update warehouse with given restock amount
                            query = "update warehouseinventory set current_amt = current_amt + %s where product_id = %s and w_ID = %s"
                            cursor.execute(query, (amount, cpresults[0], warehouselocation))
                            cnx.commit()
                            print(amount, "added to the warehouse!\n")

                        #allows user to restock more items or choose another warehouse
                        nowwhat = input("Would you like to:\nA: Restock more items to this warehouse\nB: Restock items to another warehouse\nC: Quit\n")
                        if nowwhat in ["a" or "A"]:
                            continue
                        elif nowwhat in ["b" or "B"]:
                            break
                        elif nowwhat in ["c" or "C"]:
                            sys.exit()
                            
                    break
                #if they choose to choose another warehouse before they even begin restocking, it gives them the warehouse menu again                  
                elif restockchoice in ["b", "B"]:
                    break
                else:
                    print("Please choose a valid option")


def custom():
    #set up database
    cnx = mysql.connector.connect(user='com303gcortgras', password='gc45367gc',
                              host='136.244.224.221',
                              database='com303fpegj')
    cursor = cnx.cursor()

    while True:
        inputq = input("\nPlease enter the exact query you'd like to search or type quit:\n")
        query = inputq
        if query in ["quit", "Quit"]:
            sys.exit()
        
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            for row in results:
                print(row)
        except mysql.connector.Error as err:
            print("There was an error, make sure the query is in one line!")
        
                
                    
                
                

    

def intro():
    print("~~~~~~~~~~~~~~~~~~~~~")
    print("Welcome to Costco!")
    print("~~~~~~~~~~~~~~~~~~~~~")

    #asks for membership id, for simplicity, we're only using one
    membership = input("Please enter your membership id (just use M001):\n")
    if membership == "M001":
        print("\nWelcome John Doe!\n")
        
        print("Are you Looking to:\n")
        choice = input("A) Place an Order\nB) Access the Database\nC) Restock Warehouse\nD: Input Custom Queries\n")
        
        #calls the orders code with the given membership id
        if choice == "a" or choice == "A":
            orders(membership)

        #calls the code that allows the user to see the contents of all tables
        elif choice == "b" or choice == "B":
            accessdatabase()

        #calls the code that allows vendors to restock warehouses
        elif choice == "c" or choice == "C":
            restock()

        elif choice == "d" or choice == "D":
            custom()
    else:
        print("That member doesn't exist! Please try again.")

intro()





    
