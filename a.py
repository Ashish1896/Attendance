'''a,b=[int(x) for x in input ("enter 2 number").split()]
print(a,b)
## Read 2 input from keyword in a simgle line and print product
print(type(a))
print(a*b)
'''
'''
##read 3 float number from keybord with ',' as separator and print their sum
a,b,c=[float(x)for x in input("enter 3 number ").split(',')]
print(a+b+c)
print(type(a))
'''
'''
print("hi")
print()
print("hello")
print("asish\nkumar\nsahoo")
#if we went to print anything to the console we have only on function 
''' 
#print("asish "*3)
''' print () with variable no of arguments
By default values are separated by space (print)
a,b,c=10,20,30
print(a,b,c)'''
'''
name="asish"
gf='madhubala'
print("my name is "+name+" and my gf is "+gf)
print("hello",name,'your gf is ',gf)
'''
'''
print("hello",end=' ')
print("world")
'''
'''function many variable use separator (10,20,30,40,50,sep='-')
if multiple arguments are passed to the print function then by default they are separated by space but we can change the separator by using sep parameter in print function
if multiple print statement are there and we want to print in the same line then we can use end parameter in print function

you can pass object in the print function
print(10)
print(10.5)
print("asish")
print([1,2,3])
print((1,2,3))
print({1,2,3})
print({'name':'asish','age':24})
print(None)

#i--->integer
#f--->float
#s--->string
#b--->boolean
#d-->integer
'''
'''
syntax:
---------------------------- 
a=10
print('a value is %i'%a)
print(f'A value is {a}')

s='asish'
l[10,20,30,40]
print('hello %s ... the list of item are %s '(s,l))
'''
'''
name='chotu'
gf='Aakansha'
salary=123456789.85
print('hii {x}, your gf is {y} and your wife salary is {z}'.format(x=name,y=gf,z=salary))
print('hii {}, your gf is {} and your wife salary is {}'.format(name,gf,salary))

a='chotu'
b='asish'
c=123456789.45
print(f'my name is {a} my best friend is {b} and his salary is {c}')
'''
'''
flow control
----------------------------------
the order in which all the statements are executed at runtime is known as flow control

there are 3 types of flow control
1.conditional statement or selection statement
2.iterative statement
3.Transfer statement
'''
'''
1. conditional statement or selection statement
--------------------------------------------------
if-------
syntax--------
if condition:
    statement-1
    statement-2
    statement-3
statement-4
 in the above syntax statement 1,2,3 are the part of id and statement 4 is not the part of if

'''

if False:
    print('hi')
print('bye')    

a=10
b=20
if a>b:
    print('hi')
    print('bye')
    print("asish")
    print('kumar')
    print('''sahoo''')
print("oye")    

name=input("enter a number")
if name=='abc':
    print(f'hii {name} good morining')
print(f'hii {name} good night')    