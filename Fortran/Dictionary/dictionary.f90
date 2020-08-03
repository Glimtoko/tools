module dictionary_mod
use ISO_FORTRAN_ENV
implicit none

type, public :: Dictionary_Character_Real
    character(len=100), dimension(:), allocatable :: Keys
    real(kind=real64), dimension(:), allocatable :: Values
    integer(kind=int32) :: length

    contains
        procedure, public :: get => DCR_get
        procedure, public :: put => DCR_put
end type Dictionary_Character_Real

interface Dictionary_Character_Real
    module procedure basic_constructor
end interface

contains

function basic_constructor(keys, values) result(Dictionary)
    type(Dictionary_Character_Real) :: Dictionary
    character(len=100), dimension(:), intent(in) :: keys
    real(kind=real64), dimension(:), intent(in) :: values

    if (size(keys) /= size(values)) then
        write(*,*) "Error: Keys and Value arrays must be same length"
        stop
    end if

    allocate(dictionary%Keys, source=keys)
    allocate(dictionary%Values, source=values)
    dictionary%length = size(keys)
end function

function DCR_get(this, key) result(val)
    real(kind=real64) :: val
    class(Dictionary_Character_Real), intent(in) :: this
    character(len=*), intent(in) :: key

    integer(kind=int32) :: i
    do i = 1, this%length
        if (trim(this%keys(i)) == trim(key)) then
            val = this%values(i)
            return
        end if
    end do
    write(*,*) "Error: Key '" // key // "' not found"
    stop
end function

subroutine DCR_put(this, key, val)
    class(Dictionary_Character_Real), intent(inout) :: this
    character(len=*), intent(in) :: key
    real(kind=real64), intent(in) :: val

    integer(kind=int32) :: i
    integer(kind=int32) :: idx

    idx = -1
    do i = 1, this%length
        if (trim(this%keys(i)) == trim(key)) then
            idx = i
            exit
        end if
    end do

    if (idx == -1) then
        ! Resize lists. N.b. in Fortran 2003 we can implicitly reallocate the
        ! array by simply setting it to a longer array via an array constructor
        this%keys = [this%keys, key]
        this%values = [this%values, val]
        this%length = this%length + 1
    else
        this%values(idx) = val
    end if

end subroutine

end module dictionary_mod


program test
    use dictionary_mod
    implicit none

    character(len=100), dimension(:), allocatable :: keys
    real(kind=real64), dimension(:), allocatable :: values
    type(Dictionary_Character_Real) :: d

    keys = ["A", "B", "C"]
    values = [1.2_REAL64, 3.4_REAL64, 5.0_REAL64]

    d = Dictionary_Character_Real(keys, values)
    call d%put("D", 23.0_REAL64)
    print *, d%get("A")
    print *, d%get("D")

    call d%put("A", 12.0_REAL64)
    print *, d%get("A")
end program
